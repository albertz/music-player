#ifndef MP_INTRUSIVEPTR_HPP
#define MP_INTRUSIVEPTR_HPP

#include <boost/atomic.hpp>

// boost::intrusive_ptr but safe/atomic

template<typename T>
struct IntrusivePtr {
	boost::atomic<T*> ptr;

	IntrusivePtr(T* _p = NULL) : ptr(NULL) {
		if(_p) {
			intrusive_ptr_add_ref(_p);
			ptr = _p;
		}
	}

	IntrusivePtr(const IntrusivePtr& other) : ptr(NULL) {
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

	T* get() const { return ptr; }
	T& operator*() const { return *ptr; }
	T* operator->() const { return ptr; }
	operator bool() const { return ptr; }
	bool operator==(const IntrusivePtr& other) const { return ptr == other.ptr; }
	bool operator!=(const IntrusivePtr& other) const { return ptr != other.ptr; }

	IntrusivePtr& swap(IntrusivePtr&& other) {
		T* old = ptr.exchange(other.ptr);
		other.ptr = old;
		return other;
	}

	IntrusivePtr exchange(const IntrusivePtr& other) {
		IntrusivePtr old = swap(IntrusivePtr(other));
		return old;
	}

	void reset(T* _p = NULL) {
		swap(IntrusivePtr(_p));
	}
};

#endif // INTRUSIVEPTR_HPP
