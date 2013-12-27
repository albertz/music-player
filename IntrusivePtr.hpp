#ifndef MP_INTRUSIVEPTR_HPP
#define MP_INTRUSIVEPTR_HPP

#include <boost/atomic.hpp>

// boost::intrusive_ptr but safe/atomic

template<typename T>
struct IntrusivePtr {
	boost::atomic<T*> ptr;

	IntrusivePtr(T* _p = NULL) : ptr(_p) {
		if(_p)
			intrusive_ptr_add_ref(_p);
	}

	IntrusivePtr(const IntrusivePtr& other) {
		T* p = other.ptr.load();
		swap(IntrusivePtr(p));
	}

	~IntrusivePtr() {
		T* _p = ptr.exchange(NULL);
		if(_p)
			intrusive_ptr_release(_p);
	}

	IntrusivePtr& operator=(const IntrusivePtr& other) {
		T* p = other.ptr.load();
		swap(IntrusivePtr(p));
		return *this;
	}

	T& operator*() const { return *ptr; }
	T* operator->() const { return ptr; }
	operator bool() const { return ptr; }

	void swap(IntrusivePtr&& other) {
		T* old = ptr.exchange(other.ptr);
		other.ptr = old;
	}

	void reset(T* _p = NULL) {
		swap(IntrusivePtr(_p));
	}
};

#endif // INTRUSIVEPTR_HPP
