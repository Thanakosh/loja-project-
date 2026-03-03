const path = require('node:path');

const isCI = process.env.CI === 'true';
const localRunId = process.env.BUILD_RUN_ID || `${Date.now()}`;

module.exports = {
  outDir: isCI ? 'out' : path.join('out-local', `run-${localRunId}`),
  packagerConfig: {
    asar: true,
  },
  makers: [
    {
      name: '@electron-forge/maker-squirrel',
      config: {
        name: 'LojaProject',
        authors: 'Thanakosh',
        description: 'Sistema de Gerenciamento Comercial Inteligente',
      },
    },
    {
      name: '@electron-forge/maker-zip',
    },
  ],
};
