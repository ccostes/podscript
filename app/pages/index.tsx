import Head from 'next/head'
import Image from 'next/image'
import styles from '../styles/Home.module.css'
import { Auth, ThemeSupa } from '@supabase/auth-ui-react'
import { useSession, useSupabaseClient } from '@supabase/auth-helpers-react'

import Login from '../components/Login';
import Profile from '../components/Profile';

// export default function Home() {
//   const session = useSession()
//   const supabase = useSupabaseClient()
//   return (
//     <div className={styles.container}>
//       {!session ? (
//         <Auth 
//         providers={}
//         supabaseClient={supabase} 
//         appearance={{ theme: ThemeSupa }} 
//         theme="dark" />
//       ) : (
//         <p>Account page will go here.</p>
//       )}
//     </div>
//   )
// }
import { useEffect, useState } from 'react';

export default function Home() {
  const session = useSession()
  const supabase = useSupabaseClient()

  return <main>{!session ? <Login /> : <Profile session={session} />}</main>;
}
