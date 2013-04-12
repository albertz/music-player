// compile:
//   c++ portaudio-wavplay-demo.cpp -lportaudio

#include <stdio.h>
#include <portaudio.h>
#include <string>
#include <stdint.h>

#define CHECK(x) { if(!(x)) { \
fprintf(stderr, "%s:%i: failure at: %s\n", __FILE__, __LINE__, #x); \
_exit(1); } }

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
	CHECK(Pa_Initialize() == paNoError);

	PaStreamParameters outputParameters;

	outputParameters.device = Pa_GetDefaultOutputDevice();
	CHECK(outputParameters.device != paNoDevice);
	
	outputParameters.channelCount = numChannels;
	outputParameters.sampleFormat = sampleFormat;
	outputParameters.suggestedLatency = Pa_GetDeviceInfo( outputParameters.device )->defaultHighOutputLatency;
	
	PaError ret = Pa_OpenStream(
		&stream,
		NULL, // no input
		&outputParameters,
		sampleRate,
		FramesPerBuffer,
		0, // flags
		&paStreamCallback,
		NULL //void *userData
		);
	
	if(ret != paNoError) {
		fprintf(stderr, "Pa_OpenStream failed: (err %i) %s\n", ret, Pa_GetErrorText(ret));
		if(stream)
			Pa_CloseStream(stream);
		return false;
	}
	
	return true;
}

std::string freadStr(FILE* f, size_t len) {
	std::string s(len, '\0');
	CHECK(fread(&s[0], 1, len, f) == len);
	return s;
}


int main(int argc, char** argv) {
	CHECK(argc > 1);
	wavfile = fopen(argv[1], "r");
	CHECK(wavfile != NULL);
	
	CHECK(freadStr(wavfile, 4) == "RIFF");
	CHECK(portAudioOpen());
	
	fclose(wavfile);
	Pa_CloseStream(stream);
}

