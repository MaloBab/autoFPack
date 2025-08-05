<script setup>
import { computed } from 'vue'

const props = defineProps({
  titre: {
    type: String,
    required: true
  }
})

const emit = defineEmits(['ajouter'])

const titreSingulier = computed(() =>
  props.titre.endsWith('s') ? props.titre.slice(0, -1) : props.titre
)
</script>

<template>
  <div>
    <h1 class="title">{{ titre }}</h1>
    <button class="add" @click="emit('ajouter')">
      Ajouter {{ titreSingulier }}
    </button>
  </div>
</template>

<style scoped>
h1 {
  font-size: 2.5rem;          
  font-weight: 700; 
  margin-bottom: 3%;
  margin-left: 2%;
}

button {
  background-color: #2563eb;
  color: white;
  font-weight: 500;    
  font-size: 1.5rem;     
  padding: 0.75rem 1.5rem;
  margin-left: 2%;
  border-radius: 0.375rem;
  cursor: pointer;
  border: none;
}

button:hover {
  background-color: #1040e8;
}

button:focus {
  outline: none;
}

button:active {
  background: #aaa;
}
</style>