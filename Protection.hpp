#ifndef MP_PROTECTION_UNUSED_HPP
#define MP_PROTECTION_UNUSED_HPP


struct ProtectionData : boost::noncopyable {
	PyMutex mutex;
	uint16_t lockCounter;
	long lockThreadIdent;
	bool isValid;
	ProtectionData(); ~ProtectionData();
	void lock();
	void unlock();
};

typedef boost::shared_ptr<ProtectionData> ProtectionPtr;
struct Protection : boost::noncopyable {
	ProtectionPtr prot;
	Protection() : prot(new ProtectionData) {}
};

struct ProtectionScope : boost::noncopyable {
	ProtectionPtr prot;
	ProtectionScope(const Protection& p);
	~ProtectionScope();
	void setInvalid();
	bool isValid();
};

#endif // PROTECTION_UNUSED_HPP
