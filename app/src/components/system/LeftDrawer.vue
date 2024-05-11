<template>
  <v-navigation-drawer permanent>
    <v-list nav>
      <RouterLink to="/" class="router-link">
        <v-list-item prepend-icon="mdi-view-dashboard-outline" title="Dashboard" value="home"></v-list-item>
      </RouterLink>
      <RouterLink to="/about" class="router-link">
        <v-list-item prepend-icon="mdi-note-outline" title="Logs" value="about"></v-list-item>
      </RouterLink>
      <RouterLink to="/" class="router-link">
        <v-list-item prepend-icon="mdi-server" title="Carton Manager" value="manager"></v-list-item>
      </RouterLink>
      <RouterLink to="/" class="router-link">
        <v-list-item prepend-icon="mdi-camera-iris" title="Camera Settings" value="camera-settings"></v-list-item>
      </RouterLink>
    </v-list>
    <template v-slot:append>
      <div class="pa-2">
        <v-btn block prepend-icon="mdi-cog-outline">
          Settings
        </v-btn>
      </div>
    </template>
  </v-navigation-drawer>
</template>
