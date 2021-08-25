from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Response, status
from fastapi.responses import FileResponse, RedirectResponse
from pydantic import BaseModel
import pathlib
import os

app = FastAPI()
dir_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

@app.get("/")
async def docs_redirect():
    return RedirectResponse(url='/docs')

@app.post("/files/{group_id}/{domain}/", 
    status_code=status.HTTP_201_CREATED,
    summary="Upload file to the server",
    )
async def create_upload_file(group_id: int, domain: str, newfilename: Optional[str] = None, file: UploadFile = File(...)):
    """
    Receive and store a file in the given path. The path is supplied as follows:

    - **group_id**: Group id of the analysis owner
    - **domain**: Domain of the analysis
    - **newfilename**: (Optional) Name of the file
    """
    filename = newfilename or file.filename
    dirpath = f'{dir_path}/uploads/{group_id}/{domain}'
    filepath = f'{dirpath}/{filename}'

    # Create the directory if it does not exist
    if not os.path.exists(dirpath):
        pathlib.Path(os.path.join(dirpath)).mkdir(parents = True, exist_ok=True)

    # write file
    with open(f'{filepath}', 'wb') as f:
        content = await file.read()
        f.write(content)
    return {"status": "success",
            "filename": filename,
            "uploaded_to": filepath}


class HTTPError(BaseModel):
    detail: str

    class Config:
        schema_extra = {
            "example": {"detail": "HTTPException raised."},
        }


@app.get(
    "/files/{group_id}/{domain}/{filename}", 
        summary="Request file from the server",
        responses={
            status.HTTP_200_OK: {
                "content": {"application/pdf": {}},
                "description": "Return the analysis pdf.",
            },
            status.HTTP_404_NOT_FOUND : {
                "model": HTTPError,
                "description": "File not found",
            },
        }
    )
async def get_file(group_id: int, domain: str, filename: str):
    """
    Request the specified file from the server

    - **group_id**: Group id of the analysis owner
    - **domain**: Target domain of the analysis
    - **filename**: Filename of the requested analysis
    """
    dirpath = f'{dir_path}/uploads/{group_id}/{domain}'
    filepath = f'{dirpath}/{filename}'
    print(filepath, flush=True)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return FileResponse(filepath, media_type="application/pdf")