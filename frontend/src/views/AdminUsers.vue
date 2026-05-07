<template>
  <div class="admin-page">
    <div class="admin-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="openCreate">新建用户</el-button>
    </div>

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
      <el-button @click="handleSearch">搜索</el-button>
    </div>

    <!-- 用户列表 -->
    <el-table :data="users" style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="role" label="角色" width="100">
        <template #default="{ row }">
          <el-tag :type="row.role === 'admin' ? 'danger' : 'info'">
            {{ row.role === 'admin' ? '管理员' : '用户' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="row.is_active ? 'success' : 'danger'">
            {{ row.is_active ? '启用' : '禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="email" label="邮箱" width="180" />
      <el-table-column prop="full_name" label="姓名" width="120" />
      <el-table-column prop="last_login_at" label="最后登录" width="180">
        <template #default="{ row }">
          {{ row.last_login_at ? formatDate(row.last_login_at) : '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="创建时间" width="180">
        <template #default="{ row }">
          {{ formatDate(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button type="primary" size="small" @click="openEdit(row)">
            编辑
          </el-button>
          <el-button
            :type="row.is_active ? 'warning' : 'success'"
            size="small"
            @click="handleToggleStatus(row)"
          >
            {{ row.is_active ? '禁用' : '启用' }}
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
} from "@/services/admin";
import type { User, CreateUserPayload, UpdateUserPayload } from "@/types";

// 用户列表相关
const users = ref<User[]>([]);
const loading = ref(false);
const total = ref(0);
const currentPage = ref(1);
const pageSize = ref(20);

// 筛选相关
const searchQuery = ref("");
const roleFilter = ref("");

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

// 加载用户列表
const loadUsers = async () => {
  loading.value = true;
  try {
    const res = await listUsers({
      page: currentPage.value,
      size: pageSize.value,
      search: searchQuery.value || undefined,
      role: roleFilter.value || undefined,
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

onMounted(loadUsers);
</script>

<style scoped>
.admin-page {
  max-width: 1400px;
  margin: 20px auto;
  padding: 0 20px;
}
.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
