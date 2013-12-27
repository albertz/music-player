#ifndef MP_LINKEDLIST_HPP
#define MP_LINKEDLIST_HPP

#include <boost/shared_ptr.hpp>

// lockfree

template<typename T>
class LinkedList {
public:
	struct Item;
	typedef boost::shared_ptr<Item> ItemPtr;
	struct Item {
		ItemPtr next;
		T value;
	};

private:
	ItemPtr first, last;

public:
	// not thread-safe!
	struct Iterator {
		ItemPtr ptr;

		Iterator(const ItemPtr& _ptr) : ptr(_ptr) {}

		T& operator*() {
			return ptr->value;
		}

		Iterator& operator++() {
			ptr = ptr->next;
			return *this;
		}

		bool operator!=(const Iterator& other) const {
			return ptr != other.ptr;
		}
	};

	Iterator begin() {
		return Iterator(first);
	}

	Iterator end() {
		return Iterator(NULL);
	}

	// only single producer supported
	void push_back() {
		ItemPtr item(new Item());
		ItemPtr oldLast = last;
		if(!first) first = item;
		if(!last) last = item;
		else {
			last->next = item;
			last = item;
		}
	}

	// only single consumer supported
	ItemPtr pop_front() {
		if(first) {
			ItemPtr oldFirst = first;
			first = first->next;
			if(!first) last = NULL;
			return oldFirst;
		}
		return NULL;
	}

	// not multithreading safe at all
	void clear() {
		first.reset();
		last.reset();
	}

	bool empty() {
		return first == NULL;
	}

	// be very careful!
	T& front() { return first->value; }
	T& back() { return last->value; }

};


#endif // LINKEDLIST_HPP
