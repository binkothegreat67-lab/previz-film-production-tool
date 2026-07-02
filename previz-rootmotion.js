/* =============================================================================
 * previz-rootmotion.js  —  Root-motion audit & fix for Pre-Viz director monitor
 * -----------------------------------------------------------------------------
 * Stops a character (e.g. Marco) drifting/orbiting during an in-place idle by
 * flattening residual root translation, and reports exactly where any motion
 * lives so you never pin the wrong bone.
 *
 * Assumes THREE is global (typical single-file Three.js build). Plain functions,
 * no module exports — works inlined or via <script src="previz-rootmotion.js">.
 *
 * Quick use, right inside your GLTFLoader callback, BEFORE you build the mixer:
 *     fixIdleRootMotion(gltf);                 // audit → pin Hips → re-audit
 *     const mixer  = new THREE.AnimationMixer(gltf.scene);
 *     mixer.clipAction(gltf.animations[0]).play();
 *
 * If the AFTER audit shows translation still on a non-Hips track, re-run with
 * that bone:  fixIdleRootMotion(gltf, { boneRegex: /Root$/i });
 * ========================================================================== */

/* -----------------------------------------------------------------------------
 * AUDIT — lists every animated position track's X/Y/Z range and the Hips yaw
 * sweep. Flags (⚠) any track carrying real XZ translation, and any heading
 * drift > 5°. Run before and after a fix to confirm it took.
 * -------------------------------------------------------------------------- */
function auditRootMotion(clip, label = '') {
  const POS_EPS = 0.001;   // metres — below this XZ range counts as "still"
  const YAW_EPS = 5;       // degrees — above this counts as heading drift

  console.group(`[audit ${label}] "${clip.name}"  dur=${clip.duration.toFixed(2)}s  tracks=${clip.tracks.length}`);

  clip.tracks.forEach((track) => {
    // --- position tracks: report XYZ travel ---------------------------------
    if (track.name.endsWith('.position')) {
      const v = track.values, n = v.length / 3;
      let mnX = Infinity, mxX = -Infinity, mnY = Infinity, mxY = -Infinity, mnZ = Infinity, mxZ = -Infinity;
      for (let i = 0; i < n; i++) {
        const x = v[i * 3], y = v[i * 3 + 1], z = v[i * 3 + 2];
        mnX = Math.min(mnX, x); mxX = Math.max(mxX, x);
        mnY = Math.min(mnY, y); mxY = Math.max(mxY, y);
        mnZ = Math.min(mnZ, z); mxZ = Math.max(mxZ, z);
      }
      const rX = mxX - mnX, rY = mxY - mnY, rZ = mxZ - mnZ;
      const drifts = (rX > POS_EPS || rZ > POS_EPS);
      console.log(
        `${drifts ? '⚠ ' : '  '}POS  ${track.name}  ` +
        `X±${rX.toFixed(4)}  Y±${rY.toFixed(4)}  Z±${rZ.toFixed(4)}` +
        `${drifts ? '  ← carries XZ translation (pin this)' : ''}`
      );

    // --- Hips quaternion: report yaw (heading) sweep ------------------------
    } else if (track.name.endsWith('.quaternion') && /Hips\.quaternion$/i.test(track.name)) {
      const v = track.values, n = v.length / 4;
      const q = new THREE.Quaternion(), e = new THREE.Euler();
      let mnYaw = Infinity, mxYaw = -Infinity;
      for (let i = 0; i < n; i++) {
        q.set(v[i * 4], v[i * 4 + 1], v[i * 4 + 2], v[i * 4 + 3]);
        e.setFromQuaternion(q, 'YXZ');   // YXZ → .y is yaw; fine for small idle sweeps
        mnYaw = Math.min(mnYaw, e.y); mxYaw = Math.max(mxYaw, e.y);
      }
      const deg = THREE.MathUtils.radToDeg(mxYaw - mnYaw);
      const big = deg > YAW_EPS;
      console.log(
        `${big ? '⚠ ' : '  '}ROT  ${track.name}  yaw±${deg.toFixed(2)}°` +
        `${big ? '  ← heading drift (Marco turning off his mark)' : ''}`
      );
    }
  });

  console.groupEnd();
}

/* -----------------------------------------------------------------------------
 * PIN — overwrites every keyframe of one bone's position track with that bone's
 * bind (rest) pose, so it cannot translate. Reads rest straight from the bone,
 * so X/Z are correct even on rigs that carry a small offset. MUST run before the
 * mixer's action is created (mutating values after clipAction can hit a stale
 * interpolant cache). Returns the rest pose it used, or null if nothing matched.
 * -------------------------------------------------------------------------- */
function pinPositionToRest(gltf, boneRegex = /Hips$/i, clipName = null) {
  let bone = null;
  gltf.scene.traverse((o) => { if (!bone && o.isBone && boneRegex.test(o.name)) bone = o; });
  if (!bone) { console.warn('[pin] no bone matched', boneRegex); return null; }

  const rest = { x: bone.position.x, y: bone.position.y, z: bone.position.z };
  const escaped = bone.name.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  const trackRegex = new RegExp(escaped + '\\.position$');

  const clips = clipName ? gltf.animations.filter((c) => c.name === clipName) : gltf.animations;
  let touched = 0;
  clips.forEach((clip) => {
    const track = clip.tracks.find((t) => trackRegex.test(t.name));
    if (!track) return;
    const v = track.values;
    for (let i = 0; i < v.length; i += 3) { v[i] = rest.x; v[i + 1] = rest.y; v[i + 2] = rest.z; }
    touched++;
  });

  console.log(`[pin] ${bone.name} → rest`, rest, `(${touched} clip${touched === 1 ? '' : 's'})`);
  return rest;
}

/* -----------------------------------------------------------------------------
 * ONE-CALL WRAPPER — audit, pin, re-audit. This is what you normally call.
 * -------------------------------------------------------------------------- */
function fixIdleRootMotion(gltf, { boneRegex = /Hips$/i, clipName = null, verbose = true } = {}) {
  const clips = clipName ? gltf.animations.filter((c) => c.name === clipName) : gltf.animations;
  if (verbose) clips.forEach((c) => auditRootMotion(c, 'BEFORE'));
  const rest = pinPositionToRest(gltf, boneRegex, clipName);
  if (verbose) clips.forEach((c) => auditRootMotion(c, 'AFTER'));
  return rest;
}

/* -----------------------------------------------------------------------------
 * RUNTIME WATCHDOG — measures a target's WORLD position every frame against a
 * spawn mark and flags horizontal drift over a threshold. Catches drift from
 * ANY source (parent transforms, IK, retargeting) that a clip-level audit can't
 * see, because it reads the final rendered transform.
 *
 * Point `target` at the HIPS BONE (not gltf.scene) so it sees bone-level motion
 * as well as parent motion. Distances are in scene units (metres here).
 *
 *   const dog = createDriftWatchdog(hipsBone, { thresholdM: 0.005, label: 'Marco' });
 *   // ...in animate(), AFTER mixer.update(dt):
 *   dog.check();
 * -------------------------------------------------------------------------- */
function createDriftWatchdog(target, opts = {}) {
  const {
    thresholdM    = 0.005,   // 5 mm horizontal — "a few millimetres"
    axis          = 'xz',    // 'xz' = ground plane (orbit/slide), 'xyz' = include bob
    onTrip        = null,    // callback(info) the first frame it crosses threshold
    onUpdate      = null,    // callback(distM, tripped) every frame — wire to a HUD
    logThrottleMs = 1000,    // min ms between console warnings while tripped
    label         = 'target',
  } = opts;

  const mark = new THREE.Vector3();
  const cur  = new THREE.Vector3();
  let armed = false, tripped = false, peak = 0, lastLog = 0;

  function dist() {
    target.getWorldPosition(cur);      // forces ancestor matrix update before read
    if (axis === 'xyz') return cur.distanceTo(mark);
    return Math.hypot(cur.x - mark.x, cur.z - mark.z);   // horizontal only
  }

  const api = {
    // Capture the spawn mark from the current world position. Auto-called on the
    // first check() if you don't call it yourself.
    arm() {
      target.getWorldPosition(mark);
      armed = true; tripped = false; peak = 0;
      console.log(`[watchdog] armed on "${label}" @`, mark.toArray().map((n) => +n.toFixed(4)));
      return api;
    },
    // Call every frame, AFTER mixer.update(dt). Returns current drift in metres.
    check(now = performance.now()) {
      if (!armed) { api.arm(); return 0; }
      const d = dist();
      if (d > peak) peak = d;
      if (onUpdate) onUpdate(d, d > thresholdM);
      if (d > thresholdM) {
        if (!tripped) { tripped = true; if (onTrip) onTrip({ dist: d, peak, mark: mark.clone(), pos: cur.clone() }); }
        if (now - lastLog > logThrottleMs) {
          lastLog = now;
          console.warn(`[watchdog] \u26A0 "${label}" drifted ${(d * 1000).toFixed(1)}mm (peak ${(peak * 1000).toFixed(1)}mm) off mark`);
        }
      }
      return d;
    },
    reset() { tripped = false; peak = 0; lastLog = 0; return api; },
    get state() { return { armed, tripped, peak, threshold: thresholdM }; },
  };
  return api;
}

/* -----------------------------------------------------------------------------
 * OPTIONAL HUD BADGE — a tiny corner readout for the director monitor. Green +
 * live mm while locked, red when drift trips. Wire it via the watchdog's
 * onUpdate callback (see usage below). Pure DOM, no dependencies.
 * -------------------------------------------------------------------------- */
function createDriftBadge(label = 'Marco', corner = 'bottom-left') {
  const pos = {
    'bottom-left':  'bottom:12px;left:12px;',
    'bottom-right': 'bottom:12px;right:12px;',
    'top-left':     'top:12px;left:12px;',
    'top-right':    'top:12px;right:12px;',
  }[corner] || 'bottom:12px;left:12px;';
  const el = document.createElement('div');
  el.style.cssText =
    'position:fixed;z-index:9999;font:12px/1.4 ui-monospace,monospace;padding:6px 10px;' +
    'border-radius:6px;background:rgba(0,0,0,0.7);color:#7CFC8A;pointer-events:none;' +
    'transition:color .15s,background .15s;' + pos;
  el.textContent = `${label}: locked`;
  document.body.appendChild(el);
  return {
    el,
    update(distM, tripped) {
      el.textContent = `${label}: ${(distM * 1000).toFixed(1)}mm` + (tripped ? ' \u26A0 DRIFT' : '');
      el.style.color = tripped ? '#FF5C5C' : '#7CFC8A';
      el.style.background = tripped ? 'rgba(60,0,0,0.85)' : 'rgba(0,0,0,0.7)';
    },
    destroy() { el.remove(); },
  };
}
