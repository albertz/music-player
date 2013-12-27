#ifndef MP_SAMPLETYPE_HPP
#define MP_SAMPLETYPE_HPP

#include <stdint.h>


template<typename ValueT>
struct _Value {
	const ValueT value;
	_Value(const ValueT& _v) : value(_v) {}

	template<typename T=ValueT>
	T clamp(T lowerLimit, T upperLimit) {
		T res = value;
		if(res < lowerLimit) res = lowerLimit;
		if(res > upperLimit) res = upperLimit;
		return res;
	}
};
template<typename T> _Value<T> _makeValue(const T& v) { return _Value<T>(v); }

typedef float float32_t;
static_assert(sizeof(float32_t) == 4, "float32_t declaration is wrong");

#define _FloatToPCM_raw(sample) (sample * ((double) 0x8000))
#define _FloatToPCM_clampFloat(sample) \
	(_makeValue(sample).clamp<>(-1., 1.))
// guaranteed to be in right range of right type (int16_t)
#define FloatToPCM16(s) \
	((int16_t)_makeValue(_FloatToPCM_raw(_FloatToPCM_clampFloat(s))).clamp<int32_t>(-0x8000, 0x7fff))

#if defined(OUTSAMPLEFORMAT_INT16)
#define OUTSAMPLE_t int16_t
#define OUTSAMPLEFORMATSTR "int"
#define OUTSAMPLEBITLEN 16
// normed in [-1,1] range. not clamped
#define OutSampleAsFloat(sample) (((double) sample) / ((double) 0x8000))
// normed in [-0x8000,0x7fff]. not clamped
#define OutSampleAsInt(sample) sample
// guaranteed to be in right range of type OUTSAMPLE_t
#define FloatToOutSample(sample) FloatToPCM16(sample)

#else
#define OUTSAMPLE_t float32_t
#define OUTSAMPLEFORMATSTR "float"
#define OUTSAMPLEBITLEN 32
// normed in [-1,1] range. not clamped
#define OutSampleAsFloat(sample) (sample)
// normed in [-0x8000,0x7fff]. not clamped
#define OutSampleAsInt(sample) (sample * ((double) 0x8000))
// guaranteed to be in right range of type OUTSAMPLE_t
#define FloatToOutSample(sample) (_makeValue(sample).clamp<OUTSAMPLE_t>(-1., 1.))
#endif

#define OUTSAMPLEBYTELEN (OUTSAMPLEBITLEN / 8)


#endif // SAMPLETYPE_HPP
