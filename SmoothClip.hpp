#ifndef MP_SMOOTHCLIP_HPP
#define MP_SMOOTHCLIP_HPP


// see smoothClip()
struct SmoothClipCalc {
	float x1, x2;
	double a,b,c,d;
	void setX(float x1, float x2);
	double get(double x);
};


#endif // SMOOTHCLIP_HPP
