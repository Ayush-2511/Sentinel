# SENTINEL - Backup Plan (In Case of API Failure)

## If APIs Fail:
1. **Use Mock Votes:** 
   - We have pre-cached the reasoning and voting outputs for our 3 scenarios. If the live LLM API goes down, we will switch a toggle to serve the mocked JSON responses, ensuring the UI flow remains flawless.

2. **Run Simulation Manually:** 
   - The grid state can be advanced manually step-by-step to show the intended routing and resource allocation without requiring active API generation.

3. **Show Prerecorded Video:** 
   - We have a 2-minute screen recording of the system flawlessly running the `building_collapse.json` scenario. This will be queued up and ready to play at a moment's notice.

4. **Explain Architecture Confidently:** 
   - If a crash happens, pivot immediately to the architecture diagram. Explain *why* it works conceptually. Hackathon judges understand live demo bugs; they reward robust architecture and quick recovery.
