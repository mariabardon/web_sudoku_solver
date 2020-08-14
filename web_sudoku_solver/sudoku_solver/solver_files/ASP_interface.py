import subprocess
import os
import stat
from pathlib import Path
solverDir = os.path.dirname(os.path.abspath(__file__))
clingoPath = os.path.join(solverDir,"clingo")

def solve(aspLines):
    print('working directory ', os.getcwd())
    aspLines = aspLines + ['%%%%%%%%%%%%', 'display', '%%%%%%%%%%%%', 'value.']
    f=open(os.path.join(solverDir,"sudokuSolver_sample.sp"), "r+")
    content = f.read()
    f.close()
    mySolverPath = os.path.join(solverDir,"sudokuSolver.sp")
    f=open(mySolverPath,'w+')
    f.write(content + '\n'.join(aspLines))
    f.close()
    sparcPath = os.path.join(solverDir,"sparc.jar")

    st = os.stat(sparcPath)
    os.chmod(sparcPath, st.st_mode | stat.S_IEXEC)


    answerSet = subprocess.check_output(' '.join(['java','-jar', sparcPath, mySolverPath, '-A']),shell=True).decode("utf-8")
    os.popen(' '.join(['java','-jar', sparcPath, mySolverPath, '-A > sparc_output.txt']))
    chosenAnswer = answerSet.strip().split('\n\n')[0]
    entries = chosenAnswer.strip('{}').split(', ')
    return entries
