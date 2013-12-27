#ifndef MP_FADER_HPP
#define MP_FADER_HPP

#include <stdint.h>

struct PlayerObject;

struct Fader {
	uint16_t cur;
	uint16_t limit;
	int8_t inc; // -1 or 1 or 0
	Fader();
	void init(int8_t inc /* 1 for fading in, -1 for fading out */, int Samplerate);
	void frameTick();
	void finish();
	bool finished();
	double sampleFactor();
	void wait(PlayerObject* player);
};


#endif // FADER_HPP
