import subprocess, os, stat, sys, time

solverDir = os.path.dirname(os.path.abspath(__file__))
sparcPath = os.path.join(solverDir,"sparc.jar")
def solve(aspLines):
    aspLines = aspLines + ['%%%%%%%%%%%%', 'display', '%%%%%%%%%%%%', 'value.']
    f=open(os.path.join(solverDir,"sudokuSolver_sample.sp"), "r+")
    content = f.read()
    f.close()
    mySolverPath = os.path.join(solverDir,"sudokuSolver.sp")
    f=open(mySolverPath,'w+')
    f.write(content + '\n'.join(aspLines))
    f.close()


    st = os.stat(sparcPath)
    os.chmod(sparcPath, st.st_mode | stat.S_IEXEC)

    pipe = subprocess.Popen(['java','-jar', sparcPath, mySolverPath, '-A'], stdout=subprocess.PIPE)
    try:
        wait_timeout(pipe, 5)
    except RuntimeError as e:
        raise e



    answerSet = pipe.stdout.read().decode('utf-8')
    # sys.stdout.write('answerSet')
    # sys.stdout.write(answerSet)
    chosenAnswer = answerSet.strip().split('\n\n')[0]
    entries = chosenAnswer.strip('{}').split(', ')
    return entries

def wait_timeout(proc, seconds):
    """Wait for a process to finish, or raise exception after timeout"""
    start = time.time()
    end = start + seconds
    interval = min(seconds / 1000.0, .25)

    while True:
        result = proc.poll()
        if result is not None:
            return result
        if time.time() >= end:
            raise RuntimeError("Process timed out")
        time.sleep(interval)
