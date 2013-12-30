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

	void frameTick();

	void finish();
	bool finished();

	double sampleFactor() const;

	void wait(PlayerObject* player);
};


#endif // FADER_HPP
