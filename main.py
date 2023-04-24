from fastapi import FastAPI,HTTPException,UploadFile,File
from pydub import AudioSegment
import boto3
import os
from pydantic import BaseModel
from typing import Union

app = FastAPI(title="Audio Snip API 1.0")
s3 = boto3.client(
    's3', 
    aws_access_key_id='AKIATII4OHXK7VWTXJH5',
    aws_secret_access_key='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'
)
BUCKET = 'audio-snip'

class Range(BaseModel):
    start:int
    end:int

class Config(BaseModel):
    amplitude:Union[int,float]
    crop:Range



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
        file_name = 'Chola-Chola-MassTamilan.dev.mp3'
        file_key = 'uploads/Chola-Chola-MassTamilan.dev.mp3'
        s3.download_file(BUCKET,file_key,file_name)
        audio = AudioSegment.from_file(file_name,format='mp3')
    except Exception as err:
        raise HTTPException(status_code=500,detail=str(err))
    finally:
        os.remove(file_name)
    return {"status":True,"audio":len(audio)}