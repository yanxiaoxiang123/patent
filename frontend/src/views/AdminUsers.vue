<template>
  <div class="admin-page">
    <div class="admin-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="openCreate">新建用户</el-button>
    </div>
    <el-table :data="users" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="role" label="角色" width="120" />
      <el-table-column prop="created_at" label="创建时间" width="200" />
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
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

    <el-dialog v-model="createOpen" title="新建用户" width="420px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="初始密码">
          <el-input v-model="form.password" type="password" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.full_name" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createOpen = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="handleCreate"
          >创建</el-button
        >
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { listUsers, createUser, deleteUser } from "@/services/admin";

type CreateForm = {
  username: string;
  password: string;
  email?: string;
  full_name?: string;
};

const users = ref<any[]>([]);
const createOpen = ref(false);
const submitting = ref(false);
const form = ref<CreateForm>({
  username: "",
  password: "",
  email: "",
  full_name: "",
});

const loadUsers = async () => {
  try {
    const res = await listUsers();
    users.value = res.data || [];
  } catch (e) {
    ElMessage.error("加载用户列表失败");
  }
};

const openCreate = () => {
  form.value = { username: "", password: "", email: "", full_name: "" };
  createOpen.value = true;
};

const handleCreate = async () => {
  if (submitting.value) return;
  if (!form.value.username || !form.value.password) {
    ElMessage.warning("请填写用户名和初始密码");
    return;
  }
  submitting.value = true;
  try {
    await createUser(form.value);
    ElMessage.success("创建成功");
    createOpen.value = false;
    await loadUsers();
  } catch (e) {
    ElMessage.error("创建用户失败");
  } finally {
    submitting.value = false;
  }
};

const handleDelete = async (id: number) => {
  try {
    await deleteUser(id);
    ElMessage.success("删除成功");
    await loadUsers();
  } catch (e) {
    ElMessage.error("删除用户失败");
  }
};

onMounted(loadUsers);
</script>

<style scoped>
.admin-page {
  max-width: 900px;
  margin: 20px auto;
  padding: 0 20px;
}
.admin-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
</style>
