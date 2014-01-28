#ifndef MP_SMOOTHCLIP_HPP
#define MP_SMOOTHCLIP_HPP


// see smoothClip()
struct SmoothClipCalc {
	float x1, x2;
	double a,b,c,d;
	void setX(float x1, float x2);
	
	/*
	 For values y < 0, mirror.
	 For values y in [0,x1], this is just y (i.e. identity function).
	 For values y >= x2, this is just 1 (i.e. constant 1 function).
	 For y in [x1,x2], we use a cubic spline interpolation to just make it smooth.
	 Use smoothClip_setX() to set the spline factors.
	 */
	inline
	double get(double y) {
		SmoothClipCalc* s = this;
		if(y < 0) return -get(-y);
		if(y <= s->x1) return y;
		if(y >= s->x2) return 1;
		y = s->a * y*y*y + s->b * y*y + s->c * y + s->d;
		if(y <= s->x1) return s->x1;
		if(y >= 1) return 1;
		return y;
	}
};


#endif // SMOOTHCLIP_HPP
