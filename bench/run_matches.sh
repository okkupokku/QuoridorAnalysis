#!/bin/bash
cd "$(dirname "$0")"
for cfg in "pavlos 3" "pavlos 4" "pavlos 5" "georgen 3" "georgen 4" "georgen 5"; do
  set -- $cfg
  ./venv/bin/python match.py $1 $2 15 m_$1_d$2.json 14 > m_$1_d$2.log 2>&1
done
echo done > m_all.done
