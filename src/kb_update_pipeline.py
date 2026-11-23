import hashlib
import shutil
from pathlib import Path
from datetime import datetime
import subprocess
import sys
import argparse

from prompt_injection_guard import PromptInjectionGuard


class KnowledgeBaseUpdatePipeline:

    def __init__(self, kb_directory="knowledge_base"):

        self.kb_directory = Path(kb_directory)

        self.quarantine_directory = (
            self.kb_directory / "quarantine"
        )

        self.versions_directory = (
            self.kb_directory / "versions"
        )

        self.manifest_file = (
            self.kb_directory / "manifest.txt"
        )

        self.project_root = (
            Path(__file__).resolve().parent.parent
        )

        self.faiss_builder = (
            self.project_root
            / "src"
            / "kb_faiss_builder.py"
        )

        self.kb_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        self.quarantine_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        self.versions_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        self.injection_guard = (
            PromptInjectionGuard()
        )


    # ========================================================
    # FILE HASH
    # ========================================================

    def calculate_hash(self, file_path):

        sha256 = hashlib.sha256()

        with open(
            file_path,
            "rb"
        ) as file:

            for chunk in iter(
                lambda: file.read(8192),
                b""
            ):

                sha256.update(chunk)

        return sha256.hexdigest()


    # ========================================================
    # FILE VALIDATION
    # ========================================================

    def is_valid_file(self, file_path):

        allowed_extensions = {
            ".txt",
            ".md",
            ".pdf",
            ".csv"
        }

        return (
            file_path.is_file()
            and
            file_path.suffix.lower()
            in allowed_extensions
        )


    # ========================================================
    # DOCUMENT DISCOVERY
    # ========================================================

    def discover_documents(self):

        documents = []

        for file_path in self.kb_directory.iterdir():

            if file_path.is_file():

                if (
                    file_path.name
                    == self.manifest_file.name
                ):
                    continue

                documents.append(file_path)

        return documents


    # ========================================================
    # DOCUMENT VALIDATION
    # ========================================================

    def validate_documents(self, documents):

        valid = []
        invalid = []

        for file_path in documents:

            if self.is_valid_file(file_path):

                valid.append(file_path)

            else:

                invalid.append(file_path)

        return valid, invalid


    # ========================================================
    # PROMPT INJECTION SCANNING
    # ========================================================

    def scan_for_prompt_injection(
        self,
        documents
    ):

        safe_documents = []
        unsafe_documents = []

        for file_path in documents:

            try:

                with open(
                    file_path,
                    "r",
                    encoding="utf-8",
                    errors="ignore"
                ) as file:

                    content = file.read()

                result = (
                    self.injection_guard.scan(
                        content
                    )
                )

                if result["safe"]:

                    safe_documents.append(
                        file_path
                    )

                else:

                    unsafe_documents.append(
                        {
                            "file": file_path,
                            "patterns": result[
                                "detected_patterns"
                            ]
                        }
                    )

            except Exception:

                safe_documents.append(
                    file_path
                )

        return (
            safe_documents,
            unsafe_documents
        )


    # ========================================================
    # QUARANTINE INVALID FILES
    # ========================================================

    def quarantine_invalid_files(
        self,
        invalid_files
    ):

        quarantined = []

        for file_path in invalid_files:

            destination = (
                self.quarantine_directory
                / file_path.name
            )

            if destination.exists():

                destination.unlink()

            shutil.move(
                str(file_path),
                str(destination)
            )

            quarantined.append(
                destination
            )

        return quarantined


    # ========================================================
    # QUARANTINE PROMPT INJECTION FILES
    # ========================================================

    def quarantine_injection_files(
        self,
        unsafe_documents
    ):

        quarantined = []

        for item in unsafe_documents:

            file_path = item["file"]

            destination = (
                self.quarantine_directory
                / file_path.name
            )

            if destination.exists():

                destination.unlink()

            shutil.move(
                str(file_path),
                str(destination)
            )

            quarantined.append(
                {
                    "file": file_path.name,
                    "patterns": item[
                        "patterns"
                    ],
                    "quarantine_path": str(
                        destination
                    )
                }
            )

        return quarantined


    # ========================================================
    # LOAD PREVIOUS MANIFEST
    # ========================================================

    def load_previous_manifest(self):

        previous_manifest = {}

        if not self.manifest_file.exists():

            return previous_manifest

        with open(
            self.manifest_file,
            "r",
            encoding="utf-8"
        ) as file:

            for line in file:

                line = line.strip()

                if not line:
                    continue

                parts = line.split("|")

                if len(parts) >= 2:

                    filename = parts[0]
                    file_hash = parts[1]

                    previous_manifest[
                        filename
                    ] = file_hash

        return previous_manifest


    # ========================================================
    # CHANGE DETECTION
    # ========================================================

    def detect_changes(
        self,
        documents,
        previous_manifest
    ):

        new_files = []
        modified_files = []
        unchanged_files = []

        for file_path in documents:

            filename = file_path.name

            current_hash = (
                self.calculate_hash(
                    file_path
                )
            )

            if filename not in previous_manifest:

                new_files.append(
                    filename
                )

            elif (
                previous_manifest[filename]
                != current_hash
            ):

                modified_files.append(
                    filename
                )

            else:

                unchanged_files.append(
                    filename
                )

        return (
            new_files,
            modified_files,
            unchanged_files
        )


    # ========================================================
    # CREATE VERSION SNAPSHOT
    # ========================================================

    def create_snapshot(
        self,
        documents
    ):

        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        snapshot_directory = (
            self.versions_directory
            / timestamp
        )

        snapshot_directory.mkdir(
            parents=True,
            exist_ok=True
        )

        for file_path in documents:

            source = Path(
                file_path
            ).resolve()

            destination = (
                snapshot_directory
                / source.name
            )

            shutil.copy2(
                str(source),
                str(destination)
            )

        return snapshot_directory


    # ========================================================
    # LIST VERSIONS
    # ========================================================

    def list_versions(self):

        versions = []

        for directory in (
            self.versions_directory.iterdir()
        ):

            if directory.is_dir():

                versions.append(
                    directory
                )

        return sorted(
            versions,
            key=lambda path: path.name
        )


    # ========================================================
    # BUILD MANIFEST
    # ========================================================

    def build_manifest(
        self,
        documents
    ):

        lines = []

        for file_path in documents:

            file_hash = (
                self.calculate_hash(
                    file_path
                )
            )

            modified_time = (
                datetime.fromtimestamp(
                    file_path.stat().st_mtime
                ).isoformat()
            )

            lines.append(
                f"{file_path.name}|"
                f"{file_hash}|"
                f"{modified_time}"
            )

        with open(
            self.manifest_file,
            "w",
            encoding="utf-8"
        ) as file:

            file.write(
                "\n".join(lines)
            )


    # ========================================================
    # FAISS REBUILD
    # ========================================================

    def rebuild_faiss_index(self):

        if not self.faiss_builder.exists():

            return {
                "success": False,
                "message":
                    "FAISS builder not found.",
                "path":
                    str(self.faiss_builder)
            }

        try:

            result = subprocess.run(
                [
                    sys.executable,
                    str(self.faiss_builder)
                ],
                cwd=str(self.project_root),
                capture_output=True,
                text=True
            )

            if result.returncode == 0:

                return {
                    "success": True,
                    "message":
                        "FAISS KB index rebuilt successfully.",
                    "output":
                        result.stdout.strip()
                }

            return {
                "success": False,
                "message":
                    "FAISS rebuild failed.",
                "output":
                    result.stdout.strip(),
                "error":
                    result.stderr.strip()
            }

        except Exception as error:

            return {
                "success": False,
                "message":
                    "Exception while rebuilding FAISS.",
                "error":
                    str(error)
            }


    # ========================================================
    # ROLLBACK
    # ========================================================

    def rollback(
        self,
        version_name
    ):

        selected_version = (
            self.versions_directory
            / version_name
        )

        if not selected_version.exists():

            return {
                "success": False,
                "operation": "rollback",
                "message":
                    f"Version '{version_name}' not found."
            }

        if not selected_version.is_dir():

            return {
                "success": False,
                "operation": "rollback",
                "message":
                    "Selected version is not a directory."
            }

        restored_files = []

        for file_path in (
            selected_version.iterdir()
        ):

            if file_path.is_file():

                destination = (
                    self.kb_directory
                    / file_path.name
                )

                shutil.copy2(
                    str(file_path),
                    str(destination)
                )

                restored_files.append(
                    file_path.name
                )

        # Rebuild manifest after rollback
        documents = (
            self.discover_documents()
        )

        valid_documents, _ = (
            self.validate_documents(
                documents
            )
        )

        self.build_manifest(
            valid_documents
        )

        # Rebuild FAISS after rollback
        faiss_result = (
            self.rebuild_faiss_index()
        )

        return {
            "success": True,
            "operation": "rollback",
            "version": version_name,
            "restored_files": restored_files,
            "manifest_created":
                self.manifest_file.exists(),
            "faiss_rebuild":
                faiss_result
        }


    # ========================================================
    # NORMAL UPDATE PIPELINE
    # ========================================================

    def run(self):

        previous_manifest = (
            self.load_previous_manifest()
        )

        documents = (
            self.discover_documents()
        )

        valid, invalid = (
            self.validate_documents(
                documents
            )
        )

        quarantined_invalid = (
            self.quarantine_invalid_files(
                invalid
            )
        )

        (
            safe_documents,
            unsafe_documents
        ) = self.scan_for_prompt_injection(
            valid
        )

        quarantined_injection = (
            self.quarantine_injection_files(
                unsafe_documents
            )
        )

        (
            new_files,
            modified_files,
            unchanged_files
        ) = self.detect_changes(
            safe_documents,
            previous_manifest
        )

        snapshot = self.create_snapshot(
            safe_documents
        )

        self.build_manifest(
            safe_documents
        )

        kb_changed = bool(
            new_files
            or modified_files
            or quarantined_invalid
            or quarantined_injection
        )

        faiss_result = None

        if kb_changed:

            faiss_result = (
                self.rebuild_faiss_index()
            )

        return {

            "discovered":
                len(documents),

            "valid":
                len(valid),

            "invalid":
                len(invalid),

            "quarantined_invalid":
                len(quarantined_invalid),

            "prompt_injection_detected":
                len(unsafe_documents),

            "quarantined_injection":
                quarantined_injection,

            "new":
                new_files,

            "modified":
                modified_files,

            "unchanged":
                unchanged_files,

            "snapshot":
                snapshot.name,

            "manifest_created":
                self.manifest_file.exists(),

            "faiss_rebuild_triggered":
                kb_changed,

            "faiss_rebuild":
                faiss_result
        }


# ============================================================
# COMMAND-LINE INTERFACE
# ============================================================

def main():

    parser = argparse.ArgumentParser(
        description=
        "Knowledge Base Update Pipeline"
    )

    parser.add_argument(
        "--rollback",
        type=str,
        help=
        "Rollback KB to the specified version."
    )

    args = parser.parse_args()

    pipeline = (
        KnowledgeBaseUpdatePipeline()
    )

    if args.rollback:

        result = pipeline.rollback(
            args.rollback
        )

    else:

        result = pipeline.run()

    print(result)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    main()