// functions/.eslintrc.js
module.exports = {
  root: true,
  env: { node: true, es2020: true },
  extends: ["eslint:recommended", "google"],
  rules: {
    "require-jsdoc": "off",
    "object-curly-spacing": ["error", "always"],
    "max-len": ["error", { code: 120, ignoreStrings: true, ignoreTemplateLiterals: true }],
    "quotes": ["error", "double", { avoidEscape: true }],
    "indent": ["error", 2, { "SwitchCase": 1 }],
    "no-multi-spaces": "off",
    "comma-dangle": "off", // <- desactiva la coma final obligatoria
  },
};
