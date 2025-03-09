import React from 'react';
import { Chat } from './components/Chat';
import { AuroraBackground } from "./components/ui/aurora-background";
import { motion } from "motion/react";

function App() {
  return (
    <div className="relative min-h-screen">
      <Chat />
    </div>
  );
}

export default App;