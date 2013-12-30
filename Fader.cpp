
#include "ffmpeg.h" // for Player, used in Fader::wait()
#include "PyThreading.hpp" // used in Fader::wait()

#include <assert.h>
#include "Fader.hpp"



Fader::Fader() {
	cur = limit = 0;
	inc = 0;
}

#define FADE_TIME 50 // in ms

void Fader::change(int8_t _inc, int Samplerate) {
	uint16_t newLimit = Samplerate * FADE_TIME / 1000;
	bool _finished = finished();
	uint16_t oldLimit = limit.exchange(newLimit);
	inc = _inc;
	if(oldLimit != newLimit || _finished) {
		if(_inc >= 0) cur = 0;
		else cur = newLimit;
	}
}

void Fader::frameTick() {
	if(finished()) return;
	cur += inc;
}

void Fader::finish() {
	if(inc < 0) cur = 0;
	else cur = limit.load();
}

bool Fader::finished() {
	int8_t incCpy(inc);
	if(incCpy == 0) return true;
	if(incCpy > 0) return cur >= limit;
	if(incCpy < 0) return cur == 0;
	assert(false); return false;
}

double Fader::sampleFactor() const {
	if(limit == 0) return 1;
	return double(cur) / limit;
}

void Fader::wait(PlayerObject* player) {
	// We expect to have the PlayerObject lock here.
	while(!finished()) {
		PyScopedUnlock(player->lock);
		usleep(10000);
	}
}

