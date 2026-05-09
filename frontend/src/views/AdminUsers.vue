<template>
  <div class="admin-page">
    <div class="admin-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="openCreate">新建用户</el-button>
    </div>

    <el-tabs v-model="activeTab" class="admin-tabs">
      <!-- 用户列表 Tab -->
      <el-tab-pane label="用户列表" name="users">
        <!-- 搜索和筛选 -->
        <div class="filter-bar">
          <el-input
            v-model="searchQuery"
            placeholder="搜索用户名..."
            style="width: 200px"
            clearable
            @clear="handleSearch"
          />
          <el-select
            v-model="roleFilter"
            placeholder="角色筛选"
            style="width: 120px"
            clearable
            @change="handleSearch"
          >
            <el-option label="全部" value="" />
            <el-option label="管理员" value="admin" />
            <el-option label="用户" value="user" />
          </el-select>
          <el-select
            v-model="activityFilter"
            placeholder="活动状态"
            style="width: 150px"
            clearable
            @change="handleSearch"
          >
            <el-option label="全部" value="" />
            <el-option label="7天未登录" value="active_7d" />
            <el-option label="30天未登录" value="active_30d" />
            <el-option label="从未登录" value="never_login" />
          </el-select>
          <el-button @click="handleSearch">搜索</el-button>
        </div>

        <!-- 批量操作工具栏 -->
        <div class="batch-toolbar" v-if="selectedUsers.length > 0">
          <el-badge :value="selectedUsers.length" type="primary">
            <span class="selected-label">已选择 {{ selectedUsers.length }} 个用户</span>
          </el-badge>
          <el-button size="small" @click="handleBatchEnable">批量启用</el-button>
          <el-button size="small" @click="handleBatchDisable">批量禁用</el-button>
          <el-button size="small" type="warning" @click="openBatchResetPassword">批量重置密码</el-button>
          <el-button size="small" type="danger" @click="openBatchDelete">批量删除</el-button>
          <el-button size="small" @click="handleExport">导出</el-button>
        </div>

        <!-- 用户列表 -->
        <el-table
          v-loading="loading"
          :data="users"
          style="width: 100%"
          @selection-change="handleSelectionChange"
        >
          <el-table-column type="selection" width="50" />
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="username" label="用户名" />
          <el-table-column prop="role" label="角色" width="100">
            <template #default="{ row }">
              <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">
                {{ row.role === "admin" ? "管理员" : "用户" }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.is_active ? 'success' : 'danger'">
                {{ row.is_active ? "启用" : "禁用" }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="email" label="邮箱" width="180" />
          <el-table-column prop="full_name" label="姓名" width="120" />
          <el-table-column prop="document_count" label="文档数量" width="100">
            <template #default="{ row }">
              {{ row.document_count ?? "-" }}
            </template>
          </el-table-column>
          <el-table-column prop="session_count" label="会话数量" width="100">
            <template #default="{ row }">
              {{ row.session_count ?? "-" }}
            </template>
          </el-table-column>
          <el-table-column prop="last_login_at" label="最后登录" width="180">
            <template #default="{ row }">
              {{ row.last_login_at ? formatDate(row.last_login_at) : "-" }}
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="300" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" size="small" @click="openEdit(row)">
                编辑
              </el-button>
              <el-button
                :type="row.is_active ? 'warning' : 'success'"
                size="small"
                @click="handleToggleStatus(row)"
              >
                {{ row.is_active ? "禁用" : "启用" }}
              </el-button>
              <el-button size="small" @click="openUserStats(row)">
                详情
              </el-button>
              <el-popconfirm
                title="确定删除该用户？"
                @confirm="handleDelete(row.id)"
              >
                <template #reference>
                  <el-button type="danger" size="small">删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="currentPage"
            v-model:page-size="pageSize"
            :total="total"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @current-change="loadUsers"
            @size-change="loadUsers"
          />
        </div>
      </el-tab-pane>

      <!-- 操作日志 Tab -->
      <el-tab-pane label="操作日志" name="audit">
        <!-- 审计日志筛选 -->
        <div class="filter-bar">
          <el-select
            v-model="auditActionFilter"
            placeholder="操作类型"
            style="width: 140px"
            clearable
            @change="loadAuditLogs"
          >
            <el-option label="全部" value="" />
            <el-option label="创建" value="CREATE" />
            <el-option label="删除" value="DELETE" />
            <el-option label="启用" value="ENABLE" />
            <el-option label="禁用" value="DISABLE" />
            <el-option label="重置密码" value="RESET_PWD" />
            <el-option label="更新" value="UPDATE" />
            <el-option label="批量创建" value="BATCH_CREATE" />
            <el-option label="批量删除" value="BATCH_DELETE" />
            <el-option label="批量启用" value="BATCH_ENABLE" />
            <el-option label="批量禁用" value="BATCH_DISABLE" />
            <el-option label="批量重置密码" value="BATCH_RESET_PWD" />
          </el-select>
          <el-date-picker
            v-model="auditDateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            style="width: 260px"
            @change="loadAuditLogs"
          />
          <el-button @click="loadAuditLogs">搜索</el-button>
          <el-button @click="handleExportAuditLogs">导出审计日志</el-button>
        </div>

        <!-- 审计日志列表 -->
        <el-table v-loading="auditLoading" :data="auditLogs" style="width: 100%">
          <el-table-column prop="created_at" label="操作时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="operator_username" label="操作人" width="120" />
          <el-table-column prop="action" label="操作类型" width="120">
            <template #default="{ row }">
              <el-tag :type="getActionTagType(row.action)">
                {{ formatAction(row.action) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="target_username" label="目标用户" width="120">
            <template #default="{ row }">
              {{ row.target_username ?? "-" }}
            </template>
          </el-table-column>
          <el-table-column prop="ip_address" label="IP地址" width="140">
            <template #default="{ row }">
              {{ row.ip_address ?? "-" }}
            </template>
          </el-table-column>
          <el-table-column prop="detail" label="详情">
            <template #default="{ row }">
              {{ formatDetail(row.detail) }}
            </template>
          </el-table-column>
        </el-table>

        <!-- 审计日志分页 -->
        <div class="pagination-wrapper">
          <el-pagination
            v-model:current-page="auditCurrentPage"
            v-model:page-size="auditPageSize"
            :total="auditTotal"
            :page-sizes="[10, 20, 50]"
            layout="total, sizes, prev, pager, next"
            @current-change="loadAuditLogs"
            @size-change="loadAuditLogs"
          />
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- 新建用户对话框 -->
    <el-dialog v-model="createOpen" title="新建用户" width="450px">
      <el-form :model="createForm" label-width="100px" :rules="createRules">
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="createForm.username"
            placeholder="3-50位字母、数字、下划线"
          />
        </el-form-item>
        <el-form-item label="初始密码" prop="password">
          <el-input
            v-model="createForm.password"
            type="password"
            placeholder="至少8位，包含大小写字母和数字"
          />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="createForm.email" placeholder="可选" />
        </el-form-item>
        <el-form-item label="姓名" prop="full_name">
          <el-input v-model="createForm.full_name" placeholder="可选" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="createForm.role" style="width: 100%">
            <el-option label="用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createOpen = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreate">
          创建
        </el-button>
      </template>
    </el-dialog>

    <!-- 编辑用户对话框 -->
    <el-dialog v-model="editOpen" title="编辑用户" width="450px">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" disabled />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="editForm.full_name" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="editForm.role" style="width: 100%">
            <el-option label="用户" value="user" />
            <el-option label="管理员" value="admin" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editOpen = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleUpdate">
          保存
        </el-button>
      </template>
    </el-dialog>

    <!-- 用户详情对话框 -->
    <el-dialog v-model="statsOpen" title="用户详情" width="600px">
      <el-descriptions :column="2" border v-if="statsData">
        <el-descriptions-item label="用户名">{{ statsData.username }}</el-descriptions-item>
        <el-descriptions-item label="文档数量">{{ statsData.document_count }}</el-descriptions-item>
        <el-descriptions-item label="会话数量">{{ statsData.session_count }}</el-descriptions-item>
        <el-descriptions-item label="最近登录">
          {{ statsData.last_login_at ? formatDate(statsData.last_login_at) : "从未登录" }}
        </el-descriptions-item>
        <el-descriptions-item label="最后登录IP">
          {{ statsData.last_login_ip || "-" }}
        </el-descriptions-item>
      </el-descriptions>

      <div class="login-history-section" v-if="loginHistory.length > 0">
        <h4>登录历史</h4>
        <el-table :data="loginHistory" size="small" max-height="200">
          <el-table-column prop="created_at" label="时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="ip_address" label="IP地址" width="140">
            <template #default="{ row }">
              {{ row.ip_address ?? "-" }}
            </template>
          </el-table-column>
          <el-table-column prop="login_status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="row.login_status === 'success' ? 'success' : 'danger'" size="small">
                {{ row.login_status === "success" ? "成功" : "失败" }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="fail_reason" label="失败原因">
            <template #default="{ row }">
              {{ row.fail_reason ?? "-" }}
            </template>
          </el-table-column>
        </el-table>
      </div>
      <template #footer>
        <el-button @click="statsOpen = false">关闭</el-button>
      </template>
    </el-dialog>

    <!-- 批量重置密码对话框 -->
    <el-dialog v-model="batchResetPasswordOpen" title="批量重置密码" width="400px">
      <el-form :model="batchResetPasswordForm" label-width="100px">
        <el-form-item label="新密码">
          <el-input
            v-model="batchResetPasswordForm.password"
            type="password"
            placeholder="请输入新密码"
          />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input
            v-model="batchResetPasswordForm.confirmPassword"
            type="password"
            placeholder="请再次输入新密码"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="batchResetPasswordOpen = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleBatchResetPassword">
          确认
        </el-button>
      </template>
    </el-dialog>

    <!-- 批量删除确认对话框 -->
    <el-dialog v-model="batchDeleteOpen" title="批量删除确认" width="400px">
      <p>确定要删除选中的 <strong>{{ selectedUsers.length }}</strong> 个用户吗？此操作不可恢复。</p>
      <template #footer>
        <el-button @click="batchDeleteOpen = false">取消</el-button>
        <el-button type="danger" :loading="submitting" @click="handleBatchDelete">
          确认删除
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import { ElMessage, FormRules } from "element-plus";
import {
  listUsers,
  createUser,
  updateUser,
  deleteUser,
  toggleUserStatus,
  batchDeleteUsers,
  batchToggleStatus,
  batchResetPassword,
  getUserStats,
  getLoginHistory,
  getAuditLogs,
  exportUsers,
  exportAuditLogs,
  type UserStats,
  type LoginHistoryRecord,
  type AuditLogRecord,
} from "@/services/admin";
import type { User, CreateUserPayload, UpdateUserPayload } from "@/types";

// Tab 控制
const activeTab = ref("users");

// 用户列表相关
const users = ref<User[]>([]);
const loading = ref(false);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);

// 批量选择
const selectedUsers = ref<User[]>([]);

// 筛选相关
const searchQuery = ref("");
const roleFilter = ref("");
const activityFilter = ref("");

// 新建对话框
const createOpen = ref(false);
const submitting = ref(false);
const createForm = ref<CreateUserPayload>({
  username: "",
  password: "",
  email: "",
  full_name: "",
  role: "user",
});

// 编辑对话框
const editOpen = ref(false);
const editForm = ref<UpdateUserPayload & { username: string }>({
  username: "",
  email: "",
  full_name: "",
  role: "user",
});
const editingUserId = ref<number | null>(null);

// 用户详情对话框
const statsOpen = ref(false);
const statsData = ref<UserStats | null>(null);
const loginHistory = ref<LoginHistoryRecord[]>([]);

// 批量重置密码对话框
const batchResetPasswordOpen = ref(false);
const batchResetPasswordForm = ref({
  password: "",
  confirmPassword: "",
});

// 批量删除对话框
const batchDeleteOpen = ref(false);

// 审计日志相关
const auditLogs = ref<AuditLogRecord[]>([]);
const auditLoading = ref(false);
const auditTotal = ref(0);
const auditCurrentPage = ref(1);
const auditPageSize = ref(20);
const auditActionFilter = ref("");
const auditDateRange = ref<[string, string] | null>(null);

// 创建表单验证规则
const createRules: FormRules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    {
      pattern: /^[a-zA-Z0-9_]+$/,
      message: "仅支持字母、数字、下划线",
      trigger: "blur",
    },
    { min: 3, max: 50, message: "用户名长度为3-50位", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请输入初始密码", trigger: "blur" },
    { min: 6, message: "密码至少6位", trigger: "blur" },
  ],
};

// 格式化日期
const formatDate = (dateStr: string): string => {
  if (!dateStr) return "-";
  const date = new Date(dateStr);
  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
};

// 格式化操作类型
const formatAction = (action: string): string => {
  const actionMap: Record<string, string> = {
    CREATE: "创建",
    DELETE: "删除",
    ENABLE: "启用",
    DISABLE: "禁用",
    RESET_PWD: "重置密码",
    UPDATE: "更新",
    BATCH_CREATE: "批量创建",
    BATCH_DELETE: "批量删除",
    BATCH_ENABLE: "批量启用",
    BATCH_DISABLE: "批量禁用",
    BATCH_RESET_PWD: "批量重置密码",
  };
  return actionMap[action] || action;
};

// 获取操作类型标签颜色
const getActionTagType = (action: string): string => {
  const typeMap: Record<string, string> = {
    CREATE: "success",
    DELETE: "danger",
    ENABLE: "success",
    DISABLE: "warning",
    RESET_PWD: "warning",
    UPDATE: "primary",
    BATCH_CREATE: "success",
    BATCH_DELETE: "danger",
    BATCH_ENABLE: "success",
    BATCH_DISABLE: "warning",
    BATCH_RESET_PWD: "warning",
  };
  return typeMap[action] || "info";
};

// 格式化详情
const formatDetail = (detail: Record<string, unknown> | null): string => {
  if (!detail) return "-";
  if (typeof detail === "object") {
    return JSON.stringify(detail);
  }
  return String(detail);
};

// 加载用户列表
const loadUsers = async () => {
  loading.value = true;
  try {
    const res = await listUsers({
      page: currentPage.value,
      size: pageSize.value,
      search: searchQuery.value || undefined,
      role: roleFilter.value || undefined,
      activity_status: activityFilter.value || undefined,
    });
    users.value = res.data || [];
    total.value = res.total || 0;
  } catch (e: any) {
    ElMessage.error(e?.message || "加载用户列表失败");
  } finally {
    loading.value = false;
  }
};

// 搜索
const handleSearch = () => {
  currentPage.value = 1;
  loadUsers();
};

// 批量选择变化
const handleSelectionChange = (selection: User[]) => {
  selectedUsers.value = selection;
};

// 打开新建对话框
const openCreate = () => {
  createForm.value = {
    username: "",
    password: "",
    email: "",
    full_name: "",
    role: "user",
  };
  createOpen.value = true;
};

// 创建用户
const handleCreate = async () => {
  if (submitting.value) return;
  if (!createForm.value.username || !createForm.value.password) {
    ElMessage.warning("请填写用户名和初始密码");
    return;
  }
  if (!/^[a-zA-Z0-9_]+$/.test(createForm.value.username)) {
    ElMessage.warning("用户名仅支持字母、数字、下划线");
    return;
  }
  if (createForm.value.password.length < 6) {
    ElMessage.warning("密码至少6位");
    return;
  }
  submitting.value = true;
  try {
    await createUser(createForm.value);
    ElMessage.success("创建成功");
    createOpen.value = false;
    await loadUsers();
  } catch (e: any) {
    ElMessage.error(e?.message || "创建用户失败");
  } finally {
    submitting.value = false;
  }
};

// 打开编辑对话框
const openEdit = (user: User) => {
  editingUserId.value = user.id;
  editForm.value = {
    username: user.username,
    email: user.email || "",
    full_name: user.full_name || "",
    role: user.role,
  };
  editOpen.value = true;
};

// 更新用户
const handleUpdate = async () => {
  if (submitting.value || !editingUserId.value) return;
  submitting.value = true;
  try {
    await updateUser(editingUserId.value, {
      email: editForm.value.email || undefined,
      full_name: editForm.value.full_name || undefined,
      role: editForm.value.role,
    });
    ElMessage.success("更新成功");
    editOpen.value = false;
    await loadUsers();
  } catch (e: any) {
    ElMessage.error(e?.message || "更新用户失败");
  } finally {
    submitting.value = false;
  }
};

// 切换用户状态
const handleToggleStatus = async (user: User) => {
  try {
    await toggleUserStatus(user.id);
    ElMessage.success(user.is_active ? "已禁用该用户" : "已启用该用户");
    await loadUsers();
  } catch (e: any) {
    ElMessage.error(e?.message || "操作失败");
  }
};

// 删除用户
const handleDelete = async (id: number) => {
  try {
    await deleteUser(id);
    ElMessage.success("删除成功");
    await loadUsers();
  } catch (e: any) {
    ElMessage.error(e?.message || "删除用户失败");
  }
};

// 打开用户详情
const openUserStats = async (user: User) => {
  statsOpen.value = true;
  statsData.value = null;
  loginHistory.value = [];
  try {
    const stats = await getUserStats(user.id);
    statsData.value = stats;
    // 获取登录历史
    const historyRes = await getLoginHistory(user.id, 1, 5);
    loginHistory.value = historyRes.data || [];
  } catch (e: any) {
    ElMessage.error(e?.message || "加载用户详情失败");
  }
};

// 批量启用
const handleBatchEnable = async () => {
  if (selectedUsers.value.length === 0) return;
  const userIds = selectedUsers.value.map((u) => u.id);
  try {
    const res = await batchToggleStatus(userIds, true);
    ElMessage.success(`已启用 ${res.updated_count} 个用户`);
    selectedUsers.value = [];
    await loadUsers();
  } catch (e: any) {
    ElMessage.error(e?.message || "批量启用失败");
  }
};

// 批量禁用
const handleBatchDisable = async () => {
  if (selectedUsers.value.length === 0) return;
  const userIds = selectedUsers.value.map((u) => u.id);
  try {
    const res = await batchToggleStatus(userIds, false);
    ElMessage.success(`已禁用 ${res.updated_count} 个用户`);
    selectedUsers.value = [];
    await loadUsers();
  } catch (e: any) {
    ElMessage.error(e?.message || "批量禁用失败");
  }
};

// 打开批量重置密码对话框
const openBatchResetPassword = () => {
  batchResetPasswordForm.value = {
    password: "",
    confirmPassword: "",
  };
  batchResetPasswordOpen.value = true;
};

// 批量重置密码
const handleBatchResetPassword = async () => {
  if (!batchResetPasswordForm.value.password) {
    ElMessage.warning("请输入新密码");
    return;
  }
  if (batchResetPasswordForm.value.password !== batchResetPasswordForm.value.confirmPassword) {
    ElMessage.warning("两次输入的密码不一致");
    return;
  }
  if (batchResetPasswordForm.value.password.length < 6) {
    ElMessage.warning("密码至少6位");
    return;
  }
  if (selectedUsers.value.length === 0) return;
  const userIds = selectedUsers.value.map((u) => u.id);
  try {
    const res = await batchResetPassword(userIds, batchResetPasswordForm.value.password);
    ElMessage.success(`已重置 ${res.updated_count} 个用户密码`);
    batchResetPasswordOpen.value = false;
    selectedUsers.value = [];
  } catch (e: any) {
    ElMessage.error(e?.message || "批量重置密码失败");
  }
};

// 打开批量删除对话框
const openBatchDelete = () => {
  batchDeleteOpen.value = true;
};

// 批量删除
const handleBatchDelete = async () => {
  if (selectedUsers.value.length === 0) return;
  const userIds = selectedUsers.value.map((u) => u.id);
  try {
    const res = await batchDeleteUsers(userIds);
    ElMessage.success(`已删除 ${res.deleted_count} 个用户`);
    batchDeleteOpen.value = false;
    selectedUsers.value = [];
    await loadUsers();
  } catch (e: any) {
    ElMessage.error(e?.message || "批量删除失败");
  }
};

// 导出用户
const handleExport = () => {
  const url = exportUsers({
    search: searchQuery.value || undefined,
    role: roleFilter.value || undefined,
    activity_status: activityFilter.value || undefined,
  });
  window.open(url, "_blank");
};

// 加载审计日志
const loadAuditLogs = async () => {
  auditLoading.value = true;
  try {
    const params: {
      page: number;
      size: number;
      action?: string;
      start_date?: string;
      end_date?: string;
    } = {
      page: auditCurrentPage.value,
      size: auditPageSize.value,
    };
    if (auditActionFilter.value) {
      params.action = auditActionFilter.value;
    }
    if (auditDateRange.value && auditDateRange.value.length === 2) {
      params.start_date = auditDateRange.value[0];
      params.end_date = auditDateRange.value[1];
    }
    const res = await getAuditLogs(params);
    auditLogs.value = res.data || [];
    auditTotal.value = res.meta?.total || 0;
  } catch (e: any) {
    ElMessage.error(e?.message || "加载审计日志失败");
  } finally {
    auditLoading.value = false;
  }
};

// 导出审计日志
const handleExportAuditLogs = () => {
  const params: {
    action?: string;
    start_date?: string;
    end_date?: string;
  } = {};
  if (auditActionFilter.value) {
    params.action = auditActionFilter.value;
  }
  if (auditDateRange.value && auditDateRange.value.length === 2) {
    params.start_date = auditDateRange.value[0];
    params.end_date = auditDateRange.value[1];
  }
  const url = exportAuditLogs(params);
  window.open(url, "_blank");
};

onMounted(() => {
  loadUsers();
});
</script>

<style scoped>
.admin-page {
  max-width: 1400px;
  margin: 24px auto;
  padding: 0 24px;
}

.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.admin-header h2 {
  font-family: var(--font-display);
  font-size: 20px;
  color: var(--text-primary);
}

.admin-tabs {
  margin-bottom: 20px;
}

.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.batch-toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: var(--radius-md);
  align-items: center;
}

.selected-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-right: 8px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 20px;
}

.login-history-section {
  margin-top: 20px;
}

.login-history-section h4 {
  margin-bottom: 12px;
  font-size: 14px;
  font-weight: 600;
}

.admin-page :deep(.el-table) {
  border-radius: var(--radius-lg);
}

.admin-page :deep(.el-table th) {
  background: var(--bg-tertiary) !important;
  font-weight: 600;
}

.admin-page :deep(.el-button--small) {
  padding: 5px 12px;
}

.admin-page :deep(.el-input) {
  --el-input-border-radius: var(--radius-md);
}

.admin-page :deep(.el-select) {
  --el-select-border-color-hover: var(--primary-color);
}
</style>
