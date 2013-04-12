
#include <stdio.h>
#include <portaudio.h>
#include <string>
#include <stdint.h>

const int FramesPerBuffer = 1024;
PaStream* stream;
FILE* wavfile;
int numChannels;
int sampleRate;
PaSampleFormat sampleFormat;

int paStreamCallback(
	const void *input, void *output,
	unsigned long frameCount,
	const PaStreamCallbackTimeInfo* timeInfo,
	PaStreamCallbackFlags statusFlags,
	void *userData )
{

	//(OUTSAMPLE_t*) output, frameCount * outStream->player->outNumChannels
	
	return paContinue;
}

bool portAudioOpen() {
	PaStreamParameters outputParameters;
		
	outputParameters.device = Pa_GetDefaultOutputDevice();
	if (outputParameters.device == paNoDevice) {
		fprintf(stderr, "Pa_GetDefaultOutputDevice didn't returned a device");
		return false;
	}
	outputParameters.channelCount = numChannels;
	outputParameters.sampleFormat = sampleFormat;
	outputParameters.suggestedLatency = Pa_GetDeviceInfo( outputParameters.device )->defaultHighOutputLatency;
	
	PaError ret = Pa_OpenStream(
		&stream,
		NULL, // no input
		&outputParameters,
		outSamplerate, // sampleRate
		FramesPerBuffer, // framesPerBuffer,
		0, // flags
		&paStreamCallback,
		NULL //void *userData
		);
	
	if(ret != paNoError) {
		fprintf(stderr, "Pa_OpenStream failed: (err %i) %s", ret, Pa_GetErrorText(ret));
		if(stream)
			close();
		return false;
	}
	
	return true;
}

std::string freadStr(FILE* f, size_t len) {
	std::string s(len, '\0');
	assert(fread(&s[0], 1, len, f) == len);
	return s;
}


int main(int argc, char** argv) {
	assert(argc > 1);
	wavfile = fopen(argv[1], "r");
	assert(wavfile != NULL);
	
	assert(freadStr(wavfile, 4) == "RIFF");
	assert(portAudioOpen());
	
	fclose(f);
}

