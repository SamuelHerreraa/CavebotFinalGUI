/* eslint-disable valid-jsdoc */
const functions = require("firebase-functions");
const admin = require("firebase-admin");

admin.initializeApp();

/**
 * Normaliza expiresAt a segundos.
 * Si viene en milisegundos (>= 1e12), lo divide entre 1000.
 * @param {number} expiresAt
 * @return {number}
 */
function normalizeExpires(expiresAt) {
  const v = Number(expiresAt || 0);
  if (!Number.isFinite(v)) return 0;
  return v >= 1e12 ? Math.floor(v / 1000) : Math.floor(v);
}

/**
 * Calcula expired y daysRemaining a partir de una licencia.
 * @param {Object} lic
 * @return {{expired: boolean, daysRemaining: number}}
 */
function computeSummary(lic) {
  const now = Math.floor(Date.now() / 1000);
  const active = !!lic.active;
  const expiresAt = normalizeExpires(lic.expiresAt);
  const expired = !active || now >= expiresAt;
  const daysRemaining = Math.max(0, Math.floor((expiresAt - now) / 86400));
  return { expired, daysRemaining };
}

/**
 * Trigger: cuando se crea/actualiza /licenses/{uid},
 * escribe expired y daysRemaining.
 */
exports.onLicenseWrite = functions.database
  .ref("/licenses/{uid}")
  .onWrite(async (change, context) => {
    const after = change.after.val();
    if (!after) return null; // borrado

    const { expired, daysRemaining } = computeSummary(after);
    return change.after.ref.update({
      expired,
      daysRemaining,
      lastComputedAt: admin.database.ServerValue.TIMESTAMP,
    });
  });

/**
 * Tarea programada: refresca resúmenes cada hora por si pasa el tiempo
 * sin que nadie edite el nodo.
 */
exports.refreshLicenseSummaries = functions.pubsub
  .schedule("every 60 minutes")
  .onRun(async () => {
    const snap = await admin.database().ref("licenses").once("value");
    const val = snap.val() || {};
    const updates = {};

    for (const uid of Object.keys(val)) {
      const lic = val[uid] || {};
      const { expired, daysRemaining } = computeSummary(lic);
      updates[`licenses/${uid}/expired`] = expired;
      updates[`licenses/${uid}/daysRemaining`] = daysRemaining;
      updates[`licenses/${uid}/lastComputedAt`] =
        admin.database.ServerValue.TIMESTAMP;
    }

    if (Object.keys(updates).length === 0) return null;
    return admin.database().ref().update(updates);
  });
