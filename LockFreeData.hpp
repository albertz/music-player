#ifndef MP_LOCKFREEDATA_HPP
#define MP_LOCKFREEDATA_HPP

#include <boost/atomic.hpp>
#include <boost/smart_ptr/intrusive_ref_counter.hpp>
#include <stdint.h>
#include <assert.h>
#include "IntrusivePtr.hpp"


template<typename T>
class LockFreeData {
public:
	struct Item : public boost::intrusive_ref_counter< Item, boost::thread_safe_counter > {
		T data;
		Item(const T& _d) : data(_d) {}
	};
	typedef IntrusivePtr<Item> ItemPtr;

private:
	ItemPtr ptr;

public:
	LockFreeData() : ptr(new Item(T())) {}

	ItemPtr set(const T& value) {
		return ptr.swap(ItemPtr(new Item(value)));
	}

	T load() {
		ItemPtr backup(ptr);
		return backup->data;
	}
};


struct Guard {
	enum {
		S_Idx = 1,
		S_Reading = 2,
		S_ReadFlip = 4,
		S_Writing = 8,
		S_WriteFinal = 16,
	};
	boost::atomic<uint8_t> state;

};

template<typename T>
class LockFreeData_Static {
private:
	enum {
		S_Idx = 1,
		S_Reading = 2,
		S_ReadFlip = 4,
		S_Writing = 8,
		S_WriteFinal = 16,
	};
	boost::atomic<uint8_t> state;

	const uint8_t N = 2;
	T data[N];

public:
	LockFreeData_Static() : state(0) {}

	// multiple producers supported. lock-free but waits for ongoing other writes/reads
	// returns the old value
	T set(const T& _d) {
		short curState;
		do {
			curState = state.or_fetch(S_Writing);
		} while(curState & (S_Writing|S_WriteFinal)); // anotherone currently writing, try agin

		short idx = ((curState & S_Idx) + 1) % N;
		volatile T res; // volatile to be sure we copy at the right place, i.e. right now
		res = data[idx];
		data[idx] = _d;

		curState = state.xor_fetch(S_Idx | S_Writing | S_WriteFinal);
		if(curState & S_Reading) {
			while(true) { // wait until at least one read completed
				short nextState = state.load();
				if(!(nextState & S_Reading)) break;
				if((nextState & S_ReadFlip) != (curState & S_ReadFlip)) break;
				curState = nextState;
			}
		}

		// Now, either there is no read or a current read already uses the new idx.
		// Thus we are safe to remove S_WriteFinal so that we can write again.
		state.fetch_xor(S_WriteFinal);
		return res;
	}

	// only single consumer supported. this is always wait-free
	T load() {
		short curState = state.fetch_or(S_Reading);
		assert(!(curState & S_Reading)); // only a single reader supported

		short idx = curState & S_Idx;
		volatile T res; // volatile to be sure we copy at the right place, i.e. right now
		res = data[idx];

		state.fetch_xor(S_Reading | S_ReadFlip);
		return res;
	}

};


#endif // LOCKFREEDATA_HPP
