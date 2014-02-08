#ifndef __MusicPlayer_guiQt_APP_HPP__
#define __MusicPlayer_guiQt_APP_HPP__

#include <QApplication>
#include <QThread>
#include <QMetaMethod>
#include <boost/function.hpp>
#include <assert.h>

class App : public QApplication
{
	Q_OBJECT
		
public:
	App();
	
signals:
	
public slots:
	void genericExec(boost::function<void(void)> func) {
		func();
	}

private:
	// cache this
	QMetaMethod genericExec_method;
public:
	void invokeGenericExec(boost::function<void(void)> func, Qt::ConnectionType connType) {
		if(!genericExec_method.enclosingMetaObject()) {
			QByteArray normalizedSignature = QMetaObject::normalizedSignature("genericExec(boost::function<void(void)>)");
			int methodIndex = this->metaObject()->indexOfSlot(normalizedSignature);
			assert(methodIndex >= 0);
			genericExec_method = this->metaObject()->method(methodIndex);
		}
		genericExec_method.invoke(this, connType, Q_ARG(boost::function<void(void)>, func));
	}
	
};

// WARNING: Python GIL must not be held when calling this.
// When we queue the call to the main thread and the main thread
// executes some other Python code earlier, it will deadlock.
static inline
void execInMainThread_sync(boost::function<void(void)> func) {
	if(qApp->thread() == QThread::currentThread())
		func();
	else {
		((App*) qApp)->invokeGenericExec(func, Qt::BlockingQueuedConnection);
	}
}

static inline
void execInMainThread_async(boost::function<void(void)> func) {
	((App*) qApp)->invokeGenericExec(func, Qt::QueuedConnection);
}

#endif
