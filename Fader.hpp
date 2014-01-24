#ifndef MP_FADER_HPP
#define MP_FADER_HPP

#include <stdint.h>
#include <boost/atomic.hpp>

struct PlayerObject;

class Fader {
private:
	boost::atomic<uint16_t> cur;
	boost::atomic<uint16_t> limit;
	boost::atomic<int8_t> inc; // -1 or 1 or 0
public:
	Fader();

	// If samplerate differs, it resets.
	void change(int8_t inc /* 1 for fading in, -1 for fading out */, int Samplerate);

	void finish();
	void wait(PlayerObject* player);

	void frameTick() {
		if(finished()) return;
		cur += inc;
	}

	bool finished() {
		int8_t incCpy(inc);
		if(incCpy == 0) return true;
		if(incCpy > 0) return cur >= limit;
		if(incCpy < 0) return cur == 0;
		assert(false); return false;
	}

	double sampleFactor() const {
		if(limit == 0) return 1;
		return double(cur) / limit;		
	}

};


#endif // FADER_HPP
