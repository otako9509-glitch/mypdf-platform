import uuid
import threading
from datetime import datetime
from typing import Dict, Optional, List
from enum import Enum
import json
import os


class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class Job:

    def __init__(
        self,
        job_id: str,
        operation: str,
        input_files: List[Dict[str, str]],
        status: JobStatus = JobStatus.PENDING,
        output_file: Optional[str] = None,
        error: Optional[str] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self.job_id = job_id
        self.operation = operation
        self.input_files = input_files
        self.status = status
        self.output_file = output_file
        self.error = error

        self.created_at = created_at or datetime.utcnow()
        self.updated_at = updated_at or datetime.utcnow()

    def to_dict(self) -> Dict:
        return {
            "job_id": self.job_id,
            "operation": self.operation,
            "input_files": self.input_files,
            "status": self.status.value,
            "output_file": self.output_file,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class JobService:

    def __init__(
        self,
        storage_path=r"C:\Users\ADIL\Documents\pj\storage\jobs"
    ):
        self.storage_path = storage_path

        self.jobs: Dict[str, Job] = {}

        # RLock يسمح باستدعاء دوال داخل بعضها
        self.lock = threading.RLock()

        os.makedirs(
            self.storage_path,
            exist_ok=True
        )

        self._load_jobs()

    def _load_jobs(self):

        try:

            if not os.path.exists(
                self.storage_path
            ):
                return

            for filename in os.listdir(
                self.storage_path
            ):

                if not filename.endswith(".json"):
                    continue

                path = os.path.join(
                    self.storage_path,
                    filename
                )

                try:

                    with open(
                        path,
                        "r",
                        encoding="utf-8"
                    ) as f:

                        data = json.load(f)

                    job = self._from_dict(
                        data
                    )

                    self.jobs[
                        job.job_id
                    ] = job

                except Exception as e:

                    print(
                        f"Error loading {filename}: {e}"
                    )

        except Exception as e:

            print(
                f"Error loading jobs: {e}"
            )

    def _from_dict(
        self,
        data: Dict
    ) -> Job:

        created_at = None
        updated_at = None

        try:
            if data.get("created_at"):
                created_at = datetime.fromisoformat(
                    data["created_at"].replace(
                        "Z",
                        ""
                    )
                )
        except Exception:
            pass

        try:
            if data.get("updated_at"):
                updated_at = datetime.fromisoformat(
                    data["updated_at"].replace(
                        "Z",
                        ""
                    )
                )
        except Exception:
            pass

        return Job(
            job_id=data["job_id"],
            operation=data["operation"],
            input_files=data.get(
                "input_files",
                []
            ),
            status=JobStatus(
                data.get(
                    "status",
                    "PENDING"
                )
            ),
            output_file=data.get(
                "output_file"
            ),
            error=data.get(
                "error"
            ),
            created_at=created_at,
            updated_at=updated_at,
        )

    def _save_job(
        self,
        job: Job
    ):

        path = os.path.join(
            self.storage_path,
            f"{job.job_id}.json"
        )

        temp_path = path + ".tmp"

        try:

            with open(
                temp_path,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    job.to_dict(),
                    f,
                    indent=2,
                    ensure_ascii=False
                )

            os.replace(
                temp_path,
                path
            )

        except Exception as e:

            print(
                f"Error saving job {job.job_id}: {e}"
            )

    def create_job(
        self,
        operation: str,
        input_files: List[Dict[str, str]]
    ) -> Job:

        job = Job(
            job_id=str(
                uuid.uuid4()
            ),
            operation=operation,
            input_files=input_files,
            status=JobStatus.PENDING
        )

        with self.lock:

            self.jobs[
                job.job_id
            ] = job

            self._save_job(
                job
            )

        return job

    def get_job(
        self,
        job_id: str
    ) -> Optional[Job]:

        with self.lock:

            # أهم إصلاح:
            # اقرأ آخر نسخة من disk
            path = os.path.join(
                self.storage_path,
                f"{job_id}.json"
            )

            if os.path.exists(path):

                try:

                    with open(
                        path,
                        "r",
                        encoding="utf-8"
                    ) as f:

                        data = json.load(f)

                    job = self._from_dict(
                        data
                    )

                    self.jobs[
                        job_id
                    ] = job

                    return job

                except Exception as e:

                    print(
                        f"Error reading job {job_id}: {e}"
                    )

            return self.jobs.get(
                job_id
            )

    def update_job_status(
        self,
        job_id: str,
        status: JobStatus,
        output_file: Optional[str] = None,
        error: Optional[str] = None
    ) -> Optional[Job]:

        with self.lock:

            job = self.get_job(
                job_id
            )

            if not job:
                return None

            job.status = status

            job.updated_at = (
                datetime.utcnow()
            )

            if output_file is not None:

                job.output_file = (
                    output_file
                )

            if error is not None:

                job.error = error

            self.jobs[
                job_id
            ] = job

            self._save_job(
                job
            )

            return job

    def update_job_input_files(
        self,
        job_id: str,
        input_files: List[Dict[str, str]]
    ) -> Optional[Job]:

        with self.lock:

            job = self.get_job(
                job_id
            )

            if not job:
                return None

            job.input_files = (
                input_files
            )

            job.updated_at = (
                datetime.utcnow()
            )

            self._save_job(
                job
            )

            return job

    def get_pending_jobs(
        self
    ) -> List[Job]:

        with self.lock:

            jobs = []

            for job_id in list(
                self.jobs.keys()
            ):

                job = self.get_job(
                    job_id
                )

                if (
                    job and
                    job.status ==
                    JobStatus.PENDING
                ):

                    jobs.append(job)

            return jobs

    def delete_job(
        self,
        job_id: str
    ) -> bool:

        with self.lock:

            self.jobs.pop(
                job_id,
                None
            )

            path = os.path.join(
                self.storage_path,
                f"{job_id}.json"
            )

            if os.path.exists(path):

                try:
                    os.remove(path)
                except Exception:
                    return False

            return True


job_service = JobService()