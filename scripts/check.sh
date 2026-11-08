#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v javac >/dev/null || { echo 'Java 21 JDK required: javac not found'; exit 1; }
command -v python3 >/dev/null || { echo 'Python 3 required'; exit 1; }
mkdir -p build/classes
javac -d build/classes backend/prototype/ProductMatcher.java backend/prototype/MatcherSmokeTest.java
java -cp build/classes smartcart.prototype.MatcherSmokeTest
python3 -m unittest discover -s tests -v
