# Submission

Fork URL: <!-- paste the URL of your fork here -->

## Files to commit

- [ ] `DIAGNOSIS.md`: for each fault, the command that showed it and what it said
- [ ] `fixed/` with your corrected manifests (optional: you may also patch the cluster directly)

## Questions

Answer in your own words. Where a question asks for output, paste it in a code block.

### Q1. For each of the six faults paste the one command that revealed it and the one line of its output that told you what was wrong. Which of `get`, `describe`, `logs` and `get events` answered which fault?

**Your answer:**

<!-- replace this line with your answer -->

### Q2. A pod is `Pending`, one is `ImagePullBackOff`, one is `CrashLoopBackOff` and one is `Running 0/1`. Put these four on a line from "the scheduler could not place it" to "the container ran and failed". Which component is responsible at each step?

**Your answer:**

<!-- replace this line with your answer -->

### Q3. Why did `kubectl logs` show nothing useful for the pod that could not pull its image, and what did you use instead? And for the crash-looping pod, why do you need `--previous`?

**Your answer:**

<!-- replace this line with your answer -->

### Q4. The Service had no endpoints although its pods were healthy. How do you check which pods a Service selects (one command) and why does a label typo fail silently?

**Your answer:**

<!-- replace this line with your answer -->

### Q5. The reporter pod was killed with `OOMKilled` (exit code 137). Where do you see that, what is the difference between a memory request and a memory limit, and what happens to a pod that exceeds its CPU limit instead?

**Your answer:**

<!-- replace this line with your answer -->

### Q6. Order the checks you now do on any broken workload, in the order you would do them at 3 a.m. Which one would you automate first?

**Your answer:**

<!-- replace this line with your answer -->

### Q7. Paste the output of `./verify.sh`. It must end with **ALL CHECKS PASSED**.

**Your answer:**

<!-- replace this line with your answer -->

### Q8. **Tear down.** Paste the output of `./verify-teardown.sh`. It must end with **TEARDOWN VERIFIED**.

**Your answer:**

<!-- replace this line with your answer -->
