# Brief 58: finish Brief 56 from the RunPod result

The Brief 57 cloud run finished: RTX 4090 SECURE (EUR-IS-1), pod dhc93hhfxqwvi1, 14:51-17:53 on 05 Nov, exit 0, marker
DONE; Claude's helper downloaded, checksum-verified and unpacked it into roxy3d/out10i.cloud/out10/ and deleted the pod
and volume (RunPod balance 11.62 -> 8.87). Stage times: backgrounds 3454 s, weather 878 s, foreground ~84 min, doors
~10 min, mist ~2 min, package ~1 min, videos 203 s.

Do the "Once the result is home" steps 1-5 of NOTES-57.md, i.e. the remaining Brief 56 deliverables:
- verify the result (archive/member checksums, frozen hashes, baseline compatibility vs live out10, pod audit,
  endpoint proofs, complete capture set);
- merge the payload into out10i/ (full inherited live pack + changed files; the eight mist maps at the out10i root);
- decode all 144 frames of light_loop, light_loop_2x and rain_fg: A12/B12, 143 -> 0, wet-loop wraps, alpha/depth,
  Brief 53 byte identity, manifests, decoded 1x/@2x memory; look at the sign/floodlight yourself;
- qa10/draft24-dinkdonk-production.png (1280x720: live | out10i sign crop, state A and state B);
- refresh out10i manifest/checksums/validation, write out10i-copy-list.txt (NEW/CHG, with the destination of each
  line: out10 or out10mist);
- NOTES-56.md with the true provenance (cloud 4090 for production, local only for setup/probes) and timings.
Keep the stopped local fallback out10i/_work as it is (QA scratch goes in a separate folder) and keep out10i.cloud
until Claude has promoted. Never modify out10/, out10mist/ or standby/roxy.html. Write only inside roxy3d/. No new
renders unless a check proves an output is broken - then stop and report instead of re-rendering. STATUS line, stop.
