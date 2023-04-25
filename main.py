from fastapi import FastAPI,HTTPException,UploadFile,File
from pydub import AudioSegment
import boto3
import os
from pydantic import BaseModel
from typing import Union
import tempfile
import pathlib
from enum import Enum


app = FastAPI(title="Audio Snip API 1.0")
s3 = boto3.client(
    's3', 
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)

BUCKET = 'audio-snip'

class DBMode(str,Enum):
    lose="lose"
    gain="gain"

class SupportedFormats(str,Enum):
    mp3="mp3"
    wav="wav"
    flac="flac"

class Db(BaseModel):
    value:Union[int,float]
    mode:DBMode

class CropRange(BaseModel):
    start:int
    end:int

class Config(BaseModel):
    file_name:str
    file_key:str
    amplitude:Union[Db,None] = None
    crop:CropRange
    output_format:SupportedFormats

def modify_speed(audio:AudioSegment,speed:int):
    modified_audio = audio._spawn(audio.raw_data,overrides={
        "frame_rate":int(audio.frame_rate*speed)
    })
    return modified_audio.set_frame_rate(41000)


@app.get('/')
def Welcome():
    return {"Welcome!": "AudioSnip is a user-friendly audio editing tool designed to help you easily cut and trim audio files. With AudioSnip, you can effortlessly trim unwanted parts of your audio files, such as intros, outros, or any other unwanted sections. The app supports a wide range of audio file formats, including MP3, WAV, AAC, and more, and allows you to preview your edits before saving them. Additionally, AudioSnip offers advanced editing features, such as fade-in and fade-out effects, volume adjustment, and more, to help you achieve the perfect sound for your audio projects. Whether you are a podcaster, musician, or simply want to edit your audio files for personal use, AudioSnip is the perfect audio editing tool for you."}

@app.post('/upload-file')
def upload_file(audio:UploadFile = File(...)):
    try:
        destination_path = f"uploads/{audio.filename}"
        file_path = f'https://{BUCKET}.s3.amazonaws.com/{destination_path}'
        s3.upload_fileobj(audio.file, BUCKET,destination_path)
    except Exception as err:
        raise HTTPException(status_code=500,detail=str(err))    
    return {'status':True,"url":file_path,"key":destination_path,"file_name":audio.filename}

@app.post('/edit-audio')
def edit_audio(config:Config):
    try:
        file_name = config.file_name
        file_key = config.file_key
        original_file_format:str = pathlib.Path(file_name).suffix.replace('.','')
        s3.download_file(BUCKET,file_key,file_name)
        audio = AudioSegment.from_file(file_name,format=original_file_format)
        processed_audio = audio[config.crop.start:config.crop.end]
        destination_path = ''
        url_path = ''
        with tempfile.NamedTemporaryFile(suffix=f'.{config.output_format}') as temp_file:
            new_file_name = f'{file_name}-edited.{config.output_format}'
            destination_path = f'processed/{new_file_name}'
            url_path = f'https://{BUCKET}.s3.amazonaws.com/{destination_path}'
            print(config.amplitude,"priting applitude")
            if config.amplitude:
                if config.amplitude.mode == 'gain':
                    processed_audio = processed_audio + config.amplitude.value
                if config.amplitude.mode == 'lose':
                    processed_audio = processed_audio - config.amplitude.value
            # processed_audio = modify_speed(processed_audio,0.75)
            processed_audio.export(new_file_name, format=config.output_format)
            s3.upload_file(new_file_name,BUCKET,destination_path)
    except Exception as err:
        raise HTTPException(status_code=500,detail=str(err))
    finally:
        if(os.path.exists(file_name)):
            os.remove(file_name)
        if(os.path.exists(new_file_name)):
            os.remove(new_file_name)
    return {"status":True,"url":url_path,"key":destination_path,"file_name":new_file_name}

