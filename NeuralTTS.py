# A completely innocent attempt to borrow proprietary Microsoft technology for a much better TTS experience
import requests
import websockets
import random
import asyncio
import sys
from datetime import datetime
import re

voice_dict = {'arSalma' : 'ar-EG-SalmaNeural', 'arZariyah' : 'ar-SA-ZariyahNeural', 
              'caAlba' : 'ca-ES-AlbaNeural', 'daChristel' : 'da-DK-ChristelNeural',
              'enNatasha' : 'en-AU-NatashaNeural', 'enClara' : 'en-CA-ClaraNeural',
              'enLibby' : 'en-GB-LibbyNeural', 'enMia' : 'en-GB-MiaNeural', 
              'enNeerja' : 'en-IN-NeerjaNeural', 'enAria' : 'en-US-AriaNeural',
              'enGuy' : 'en-US-GuyNeural', 'esElvira' : 'es-ES-ElviraNeural',
              'esDalia' : 'es-MX-DaliaNeural', 'fiNoora' : 'fi-FI-NooraNeural',
              'frSylvie' : 'fr-CA-SylvieNeural', 'frDenise' : 'fr-FR-DeniseNeural',
              'hiSwara' : 'hi-IN-SwaraNeural', 'itElsa' : 'it-IT-ElsaNeural',
              'jaNanami' : 'ja-JP-NanamiNeural'
              }
#Fix the time to match Americanisms
def hr_cr(hr):
    corrected = (hr - 1) % 24
    return str(corrected)

#Add zeros in the right places i.e 22:1:5 -> 22:01:05
def fr(input_string):
    corr = ''
    i = 2 - len(input_string)
    while (i > 0):
        corr += '0'
        i -= 1
    return corr + input_string

#Generate X-Timestamp all correctly formatted
def getXTime():
    now = datetime.now()
    return fr(str(now.year)) + '-' + fr(str(now.month)) + '-' + fr(str(now.day)) + 'T' + fr(hr_cr(int(now.hour))) + ':' + fr(str(now.minute)) + ':' + fr(str(now.second)) + '.' + str(now.microsecond)[:3] + 'Z'

#Async function for actually communicating with the websocket
async def transferMsTTSData(msg_content, spd, ptc, voice):
    endpoint1 = "https://azure.microsoft.com/en-gb/services/cognitive-services/text-to-speech/"

    r = requests.get(endpoint1)
    main_web_content = r.text

    #They hid the Auth key assignment for the websocket in the main body of the webpage....
    token_expr = re.compile('token: \"(.*?)\"', re.DOTALL)
    Auth_Token = re.findall(token_expr, main_web_content)[0]
    req_id = str('%032x' % random.getrandbits(128)).upper() #I don't know if it matters if we reuse these, going to generate one anyway
    endpoint2 = "wss://eastus.tts.speech.microsoft.com/cognitiveservices/websocket/v1?Authorization=" + Auth_Token +"&X-ConnectionId=" + req_id[::-1]

    async with websockets.client.connect(endpoint2, ssl=True) as client_conn:
        payload_1 = '{"context":{"system":{"name":"SpeechSDK","version":"1.12.1-rc.1","build":"JavaScript","lang":"JavaScript","os":{"platform":"Browser/Linux x86_64","name":"Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0","version":"5.0 (X11)"}}}}'
        message_1 = 'Path : speech.config\r\nX-RequestId: ' + req_id + '\r\nX-Timestamp: ' + getXTime() + '\r\nContent-Type: application/json\r\n\r\n' + payload_1
        await client_conn.send(message_1)
        
        payload_2 = '{"synthesis":{"audio":{"metadataOptions":{"sentenceBoundaryEnabled":false,"wordBoundaryEnabled":false},"outputFormat":"audio-16khz-32kbitrate-mono-mp3"}}}'
        message_2 = 'Path : synthesis.context\r\nX-RequestId: ' + req_id + '\r\nX-Timestamp: ' + getXTime() + '\r\nContent-Type: application/json\r\n\r\n' + payload_2
        await client_conn.send(message_2)
        
        payload_3 = '<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US"><voice name="' + voice + '"><mstts:express-as style="General"><prosody rate="'+spd+'%" pitch="'+ptc+'%">'+ msg_content +'</prosody></mstts:express-as></voice></speak>'
        message_3 = 'Path: ssml\r\nX-RequestId: ' + req_id + '\r\nX-Timestamp: ' + getXTime() + '\r\nContent-Type: application/ssml+xml\r\n\r\n' + payload_3
        await client_conn.send(message_3)
       
        end_resp_pat = re.compile('Path:turn.end') #Checks for close connection message
        audio_stream = b''
        #audio_string = ''
        while(True):
            response = await client_conn.recv()
            #Make sure the message isn't telling us to stop
            if (re.search(end_resp_pat, str(response)) == None):
                #Check if our response is text data or the audio bytes
                if type(response) == type(bytes()):
                    #Extract binary data
                    try:
                        start_ind = str(response).find('Path:audio')
                        #audio_string += str(response)[start_ind+14:-1]
                        audio_stream += response[start_ind-2:]
                    except:
                        pass        
            else:
                break
        filename = 'test.mp3'
        with open(filename, 'wb') as audio_out:
            audio_out.write(audio_stream)
            #print(str(audio_stream))
            #print('NOW STRING FORM')
            #print(audio_string)

async def mainSeq(say, speed, pitch, voice):
    voice = voice_dict[voice]
    await transferMsTTSData(say, speed, pitch, voice)
if __name__ == "__main__":
    if len(sys.argv) == 1:
        print(voice_dict)
    elif len(sys.argv) == 5:
        say = sys.argv[1]
        speed = sys.argv[2]
        pitch = sys.argv[3]
        voice = sys.argv[4]
        mainSeq(say, speed, pitch, voice)
    else:
        print("Incorrect arg sequence")
        quit()
