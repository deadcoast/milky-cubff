#!/bin/bash
# Comprehensive CLI test script for M|inc
# Run from python/ directory

set -e

echo "=========================================="
echo "M|inc CLI Comprehensive Test Suite"
echo "=========================================="
echo ""

# Clean up any previous test outputs
rm -rf m_inc/test_cli_demo
mkdir -p m_inc/test_cli_demo

# Test 1: Single trace processing
echo "Test 1: Single trace processing"
echo "--------------------------------"
python -m m_inc.cli \
  --trace m_inc/testdata/bff_trace_small.json \
  --output m_inc/test_cli_demo/single \
  --ticks 5 \
  --quiet

if [ -f "m_inc/test_cli_demo/single/ticks.json" ]; then
  echo "✅ Single trace processing: SUCCESS"
else
  echo "❌ Single trace processing: FAILED"
  exit 1
fi
echo ""

# Test 2: Streaming mode
echo "Test 2: Streaming mode"
echo "----------------------"
python -c "import json; data = json.load(open('m_inc/testdata/bff_trace_small.json')); print(json.dumps(data[0]))" | \
  python -m m_inc.cli \
    --stream \
    --output m_inc/test_cli_demo/stream \
    --ticks 1 \
    --quiet

if [ -f "m_inc/test_cli_demo/stream/ticks.jsonl" ]; then
  echo "✅ Streaming mode: SUCCESS"
else
  echo "❌ Streaming mode: FAILED"
  exit 1
fi
echo ""

# Test 3: Batch processing (sequential)
echo "Test 3: Batch processing (sequential)"
echo "--------------------------------------"
python -m m_inc.cli \
  --batch m_inc/testdata/batch_trace_0.json m_inc/testdata/batch_trace_1.json m_inc/testdata/batch_trace_2.json \
  --output m_inc/test_cli_demo/batch_seq \
  --ticks 3 \
  --quiet

if [ -f "m_inc/test_cli_demo/batch_seq/batch_summary.json" ]; then
  echo "✅ Batch processing (sequential): SUCCESS"
  echo "   Summary:"
  python -c "import json; s = json.load(open('m_inc/test_cli_demo/batch_seq/batch_summary.json')); print(f\"   - Total traces: {s['total_traces']}\"); print(f\"   - Successful: {s['successful']}\"); print(f\"   - Failed: {s['failed']}\")"
else
  echo "❌ Batch processing (sequential): FAILED"
  exit 1
fi
echo ""

# Test 4: Batch processing (parallel)
echo "Test 4: Batch processing (parallel)"
echo "------------------------------------"
python -m m_inc.cli \
  --batch m_inc/testdata/batch_trace_0.json m_inc/testdata/batch_trace_1.json m_inc/testdata/batch_trace_2.json \
  --output m_inc/test_cli_demo/batch_par \
  --ticks 3 \
  --parallel 2 \
  --quiet

if [ -f "m_inc/test_cli_demo/batch_par/batch_summary.json" ]; then
  echo "✅ Batch processing (parallel): SUCCESS"
  echo "   Summary:"
  python -c "import json; s = json.load(open('m_inc/test_cli_demo/batch_par/batch_summary.json')); print(f\"   - Total traces: {s['total_traces']}\"); print(f\"   - Successful: {s['successful']}\"); print(f\"   - Failed: {s['failed']}\")"
else
  echo "❌ Batch processing (parallel): FAILED"
  exit 1
fi
echo ""

# Test 5: Configuration override
echo "Test 5: Configuration with seed override"
echo "-----------------------------------------"
python -m m_inc.cli \
  --trace m_inc/testdata/bff_trace_small.json \
  --output m_inc/test_cli_demo/seed_test \
  --ticks 3 \
  --seed 42 \
  --quiet

if [ -f "m_inc/test_cli_demo/seed_test/ticks.json" ]; then
  echo "✅ Configuration override: SUCCESS"
else
  echo "❌ Configuration override: FAILED"
  exit 1
fi
echo ""

# Summary
echo "=========================================="
echo "All CLI tests passed! ✅"
echo "=========================================="
echo ""
echo "Output files created in m_inc/test_cli_demo/:"
ls -R m_inc/test_cli_demo/ | head -30
echo ""
echo "Clean up with: rm -rf m_inc/test_cli_demo"
