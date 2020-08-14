import subprocess
import os
import stat
from pathlib import Path
solverDir = os.path.dirname(os.path.abspath(__file__))
clingoPath = os.path.join(solverDir,"clingo")
sparcPath = os.path.join(solverDir,"sparc.jar")
outputPath = os.path.join(solverDir,'output.txt')
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


    st = os.stat(sparcPath)
    os.chmod(sparcPath, st.st_mode | stat.S_IEXEC)


    os.popen(' '.join(['java','-jar', sparcPath, mySolverPath, '-A >', outputPath]))
    answerSet = open(outputPath, 'r').read()
    chosenAnswer = answerSet.strip().split('\n\n')[0]
    entries = chosenAnswer.strip('{}').split(', ')
    return entries
