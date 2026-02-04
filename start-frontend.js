const { spawn } = require('child_process')
const path = require('path')

console.log('🚀 启动智能专利辅助审核系统前端...\n')

const frontendPath = path.join(__dirname, 'frontend')
const npmCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm'
const nodeModulesPath = path.join(frontendPath, 'node_modules')

// 检查是否已安装依赖
const fs = require('fs')
if (!fs.existsSync(nodeModulesPath)) {
  console.log('📦 检测到未安装依赖，正在安装...')

  const installProcess = spawn(npmCmd, ['install'], {
    cwd: frontendPath,
    stdio: 'inherit'
  })

  installProcess.on('close', (code) => {
    if (code === 0) {
      console.log('✅ 依赖安装完成\n')
      startDevServer()
    } else {
      console.error('❌ 依赖安装失败')
      process.exit(1)
    }
  })
} else {
  startDevServer()
}

function startDevServer() {
  console.log('🔧 启动开发服务器...\n')

  const devProcess = spawn(npmCmd, ['run', 'dev'], {
    cwd: frontendPath,
    stdio: 'inherit'
  })

  devProcess.on('close', (code) => {
    console.log('\n👋 前端服务已停止')
    process.exit(code)
  })

  console.log('🌐 前端服务启动中...')
  console.log('📍 访问地址: http://localhost:3000')
  console.log('📚 API 文档: http://localhost:8000/docs')
  console.log('\n按 Ctrl+C 停止服务\n')
}