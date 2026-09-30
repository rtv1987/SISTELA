import os
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from pydantic import Field

from .export_model import normalized_estimate, save_settings, settings
from .package_txt import SistelaPackageTxtExporter, validate_txt_export
from .schemas import InputModel
from .services import ServiceError, get_project


class PackageSetting(InputModel):
    parameter89: int | None = Field(default=None, ge=0, le=1)


class Hierarchy(InputModel):
    code: str = Field(default='', max_length=100)
    name: str = Field(default='', max_length=4000)


class ResourceOption(InputModel):
    flag: Literal[2,3]
    code: str = Field(min_length=1,max_length=18)
    norm: str = Field(min_length=1,max_length=30)


class RowOption(InputModel):
    mark: Literal['S','G','I'] = 'S'
    ngr: int | None = Field(default=None,ge=1,le=12)
    parameters: list[int] | None = Field(default=None,max_length=2)
    coefficients: dict[str,str] = Field(default_factory=dict)
    resources: list[ResourceOption] = Field(default_factory=list,max_length=100)


class SectionOption(Hierarchy):
    coefficients: dict[str,str] = Field(default_factory=dict)


class ExportProfile(InputModel):
    complex: Hierarchy
    object: Hierarchy
    estimate: Hierarchy
    period: str = Field(default='', max_length=6)
    filename: str = Field(default='TESTTXT', max_length=100)
    sections: dict[str,SectionOption] = Field(default_factory=dict)
    rows: dict[str,RowOption] = Field(default_factory=dict)


def export_router(session_dependency, directory):
    router=APIRouter()

    @router.get('/settings/sistela')
    def read_settings(session=Depends(session_dependency)):
        return {'parameter89':settings(session,'sistela').get('parameter89')}

    @router.put('/settings/sistela')
    def update_settings(request:PackageSetting,session=Depends(session_dependency)):
        return save_settings(session,'sistela',request.model_dump())

    @router.get('/projects/{project_id}/export/model')
    def model(project_id:str,session=Depends(session_dependency)):
        return normalized_estimate(session,project_id)

    @router.put('/projects/{project_id}/export/profile')
    def profile(project_id:str,request:ExportProfile,session=Depends(session_dependency)):
        get_project(session,project_id)
        return save_settings(session,'project:'+project_id,request.model_dump())

    @router.get('/projects/{project_id}/export/txt/validation')
    def validation(project_id:str,session=Depends(session_dependency)):
        return validate_txt_export(normalized_estimate(session,project_id))

    @router.post('/projects/{project_id}/export/txt')
    def export(project_id:str,session=Depends(session_dependency)):
        value=normalized_estimate(session,project_id)
        report=validate_txt_export(value)
        if report['errors']:
            raise ServiceError(422,report)
        data=SistelaPackageTxtExporter().export(value)
        folder=directory/'exports'/uuid4().hex
        folder.mkdir(parents=True)
        name=value['filename']+'.TXT'
        (folder/name).write_bytes(data)
        return Response(data,media_type='application/octet-stream',headers={
            'Content-Disposition':f'attachment; filename="{name}"'})

    @router.post('/exports/open-folder')
    def open_folder():
        folder=(directory/'exports').resolve()
        folder.mkdir(parents=True,exist_ok=True)
        if os.name!='nt':
            raise ServiceError(422,'Aplanko atvėrimas galimas Windows programoje.')
        os.startfile(str(folder))
        return {'opened':True}
    return router
