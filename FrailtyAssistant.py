import json
import sys
import os
from os.path import join, dirname
sys.path.append(os.path.join(os.getcwd(),'..','..'))
import watson_developer_cloud
from watson_developer_cloud import SpeechToTextV1 as SpeechToText
import requests

#For Record and Play audio
import pyaudio
import wave
from array import array
from struct import pack
from sys import byteorder


#Conversation Service
WatsonAssistantUSERNAME = os.environ.get('CONVERSATION_USERNAME','b128ddce-d3e9-4d61-80b8-37c378eee542')
WatsonAssistantPASSWORD = os.environ.get('CONVERSATION_PASSWORD','QbyfsYYu4mjF')

conversation = watson_developer_cloud.ConversationV1(username=WatsonAssistantUSERNAME, password=WatsonAssistantPASSWORD, version='2017-04-21')

workspace_id ='b62aea5d-cfcc-436d-8d4c-498ac4a0ddbc'
workspace = conversation.get_workspace(workspace_id=workspace_id, export=True)

#Text To Speech
TextSpeechUSERNAME = os.environ.get('TextSpeech_USERNAME','1bd5685a-fd86-4fb2-934a-c2558dd56e03')
TextSpeechPASSWORD = os.environ.get('TextSpeech_PASSWORD','Xbl5yYC6LdhX')

text_to_speech = watson_developer_cloud.TextToSpeechV1(username=TextSpeechUSERNAME, password=TextSpeechPASSWORD)

#Speech To Text
SpeechTextUSERNAME = os.environ.get('SpeechText_USERNAME','189b1a52-38d6-43fc-9482-47cc3823a3fb')
SpeechTextPASSWORD = os.environ.get('SpeechText_PASSWORD','cN4I5hR5vEm2')

speech_to_text = watson_developer_cloud.SpeechToTextV1(username=SpeechTextUSERNAME, password=SpeechTextPASSWORD)



# check workspace status (wait for training to complete)
print('The workspace status is: {0}'.format(workspace['status']))
if workspace['status'] == 'Available':
    print('Ready to chat!')
else:
    print('The workspace should be available shortly. Please try again in 30s.')
    print('(You can send messages, but not all functionality will be supported yet.)')





#Play audio
def playWaveAudio(filename):
    #Play the wave file
    CHUNK = 1024
    wf = wave.open(filename, 'rb')
    p = pyaudio.PyAudio()
    stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True)

    data = wf.readframes(CHUNK)

    while data != '':
        stream.write(data)
        data = wf.readframes(CHUNK)

    stream.stop_stream()
    stream.close()
    p.terminate()

#Record audio
def recordWaveAudio():
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    RECORD_SECONDS = 5
    WAVE_OUTPUT_FILENAME = "input.wav"

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, 
                    channels=CHANNELS, 
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)

    print("* done recording")

    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()


#Get the user's input
def promptMessage(question):
    # Text to Speech
    # Generate the wave audio file
    fileName = 'output.wav'
    filePath = '../documents/' + fileName

    with open(join(dirname(__file__), filePath),'wb') as audio_file:
        audio_file.write(
            text_to_speech.synthesize(question, accept='audio/wav',
                                  voice="en-US_MichaelVoice").content)
                                       
    #Play the wave audio file
    playWaveAudio(fileName)
    
    #Catch user's input
    # recordfile = raw_input() 
    print("please speak a word into the microphone")
    recordWaveAudio()
    print("done - result written to input.wav")
    
    #Speech to Text
    #Recognize the wave audio file
    inputFileName = 'input.wav'
    inputFilePath = '../documents/' + inputFileName

    with open(join(dirname(__file__), inputFilePath), 'rb') as audio_file:
        results = speech_to_text.recognize(
                        #model='zh-CN_BroadbandModel',
                        audio=audio_file,
                        content_type='audio/wav',
                        timestamps=True,
                        word_confidence=True)

    # print(json.dumps(results['results'][0]['alternatives'][0]['transcript']))  
    # print(json.dumps(results['results']))

    recordfile= ''
    for i in range (0, len(results['results'])):
            if len(results['results'][i]) > 0:
                recordfile = results['results'][i]['alternatives'][0]['transcript']
                print(recordfile)
            else: 
                recordfile= ''

    return recordfile


#Main Conversation Function
def convMessage(message, context1):
    try:
        #Set conversation context
        input_content = {'text': message}
        
        #Send message to Waston Assistant to deal with
        response = conversation.message(workspace_id=workspace_id,input=input_content, context=context1)

        results = ''
        #Get the Watson's output results
        for i in range (0, len(response['output']['text'])):
           if len(response['output']['text'][i]) > 0:
               results = results + response['output']['text'][i] + ' '
               
        if len(results) > 0:
            userAnswer = promptMessage(results)     
            convMessage(userAnswer,response['context'])   
    except Exception as e:
        print('Exceptions: %s' % e)                   
    


#Initialize the conversation
response = conversation.message(
    workspace_id=workspace_id,
    input={
        'text': 'Hello'
    }
)
#Initialize the context
context = response['context']

#Get the Watson's output results
results = response['output']['text'][0]

if len(results) > 0:
    #Get the user's input
    userAnswer = promptMessage(results)     

    #Call main conversation message function
    convMessage(userAnswer,context)   





