# Importing the modules
import threading
import sys
  
# Custom Exception Class
class MyThreadException(Exception):
    pass
  
# Custom Thread Class
class MyThread(threading.Thread):
      
    def run(self):
        """Method representing the thread's activity.
        You may override this method in a subclass. The standard run() method
        invokes the callable object passed to the object's constructor as the
        target argument, if any, with sequential and keyword arguments taken
        from the args and kwargs arguments, respectively.
        """
        self.exc = None
        try:
            if self._target:
                self._target(*self._args, **self._kwargs)
        except Exception as e:
            self.exc = e
        finally:
            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._target, self._args, self._kwargs

    def join(self):
        threading.Thread.join(self)
        # Since join() returns in caller thread
        # we re-raise the caught exception
        # if any was caught
        if self.exc:
            raise self.exc

  # Function that raises the custom exception
def someFunctionTest():
    name = threading.current_thread().name
    raise MyThreadException("An error in thread "+ name)

# Driver function
def main():
    
    # Create a new Thread t
    # Here Main is the caller thread
    t = MyThread(target=someFunctionTest)
    t.start()
      
    # Exception handled in Caller thread
    try:
        t.join()
    except Exception as e:
        print("Exception Handled in Main, Detials of the Exception:", e)
  
# Driver code
if __name__ == '__main__':
    main()