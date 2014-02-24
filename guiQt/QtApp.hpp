#ifndef __MusicPlayer_guiQt_APP_HPP__
#define __MusicPlayer_guiQt_APP_HPP__

#include <QApplication>
#include <QThread>
#include <QMetaMethod>
#include <boost/function.hpp>
#include <assert.h>


class QtApp : public QApplication
{
	Q_OBJECT
	
public:
	QtApp();
	
	inline static QtApp* instance() { return (QtApp*) qApp; }
	static bool isFork(); // checked via pid
	
signals:
	
public slots:
	void genericExec(boost::function<void(void)> func) {
		func();
	}
private:
	QMetaMethod genericExec_method; // cached
public:
	void invokeGenericExec(boost::function<void(void)> func, Qt::ConnectionType connType) {
		genericExec_method.invoke(this, connType, Q_ARG(boost::function<void(void)>, func));
	}
	
private slots:
	void handleApplicationQuit();
	
public slots:
	void openWindowViaMenu(); // gets window from sender()
	bool openMainWindow();
	bool openWindow(const std::string& name);
	void minimizeWindow();
	void closeWindow();

	void edit_cut();
	void edit_copy();
	void edit_paste();
	void edit_selectAll();

	void handlePlayerUpdate(); // basically song-change and play-pause-change
	void playPause();
	void nextSong();
	
	void debug_resetPlayer();
};

// WARNING: Python GIL must not be held when calling this.
// When we queue the call to the main thread and the main thread
// executes some other Python code earlier, it will deadlock.
static inline
void execInMainThread_sync(boost::function<void(void)> func) {
	assert(!QtApp::isFork());
	if(qApp->thread() == QThread::currentThread())
		func();
	else {
		((QtApp*) qApp)->invokeGenericExec(func, Qt::BlockingQueuedConnection);
	}
}

static inline
void execInMainThread_async(boost::function<void(void)> func) {
	((QtApp*) qApp)->invokeGenericExec(func, Qt::QueuedConnection);
}

#endif
