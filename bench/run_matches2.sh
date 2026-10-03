#!/bin/bash
cd "$(dirname "$0")"
for d in 3 4 5; do
  ./venv/bin/python match.py georgen $d 15 m_georgen_d$d.json 12 > m_georgen_d$d.log 2>&1
done
echo done > m_geo.done
