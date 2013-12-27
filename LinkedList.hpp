#ifndef MP_LINKEDLIST_HPP
#define MP_LINKEDLIST_HPP

#include <boost/shared_ptr.hpp>

// lockfree

template<typename T>
class LinkedList {
	ItemPtr first, last;

public:

	struct Item {
		boost::shared_ptr<Item> next;
		T value;
		Item(const T& _v) : value(_v) {}
	};
	typedef boost::shared_ptr<Item> ItemPtr;

	// not thread-safe!
	struct Iterator {
		ItemPtr ptr;

		Iterator(const ItemPtr& _ptr) : ptr(_ptr) {}

		Iterator& operator++() {
			ptr = ptr->next;
			return *this;
		}

		bool operator==(const Iterator& other) const {
			return ptr == other.ptr;
		}
	};

	Iterator begin() {
		return Iterator(first);
	}

	Iterator end() {
		return Iterator(NULL);
	}

	// only single producer supported
	void push_back(const T& value) {
		ItemPtr item(new Item(value));
		ItemPtr oldLast = last;
		if(!first) first = item;
		last->next = item;
		last = item;
	}

	// only single consumer supported
	ItemPtr pop_front() {
		if(first) {
			ItemPtr oldFirst = first;
			first = first->next;
			return oldFirst;
		}
		return NULL;
	}

	ItemPtr front() { return first; }
	ItemPtr back() { return last; }

};


#endif // LINKEDLIST_HPP
