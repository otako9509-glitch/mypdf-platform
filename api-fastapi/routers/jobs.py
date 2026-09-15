from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
import sys

sys.path.append(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

from services import job_service


router = APIRouter()


PROJECT_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        ".."
    )
)

OUTPUTS_PATH = os.path.join(
    PROJECT_ROOT,
    "storage",
    "outputs"
)


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str
):

    job = job_service.get_job(
        job_id
    )

    if not job:

        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    data = job.to_dict()

    result = {
        "success": True,
        "job": data,
        "status": data["status"]
    }

    if (
        data["status"] == "COMPLETED"
        and
        data.get("output_file")
    ):

        result["download_url"] = (
            f"/api/v1/jobs/"
            f"{job_id}/download"
        )

    return result


@router.get(
    "/jobs/{job_id}/download"
)
async def download_job(
    job_id: str
):

    job = job_service.get_job(
        job_id
    )

    if not job:

        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    if job.status != job_service.JobStatus.COMPLETED:

        raise HTTPException(
            status_code=409,
            detail="Job is not completed yet"
        )

    if not job.output_file:

        raise HTTPException(
            status_code=404,
            detail="Output file not found"
        )

    output_path = os.path.abspath(
        os.path.join(
            OUTPUTS_PATH,
            job.output_file
        )
    )

    output_root = os.path.abspath(
        OUTPUTS_PATH
    )

    if not (
        output_path == output_root
        or
        output_path.startswith(
            output_root + os.sep
        )
    ):

        raise HTTPException(
            status_code=400,
            detail="Invalid output path"
        )

    if not os.path.isfile(
        output_path
    ):

        raise HTTPException(
            status_code=404,
            detail="Output file does not exist"
        )

    return FileResponse(
        output_path,
        filename=os.path.basename(
            output_path
        ),
        media_type="application/pdf"
    )