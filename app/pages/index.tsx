import Head from 'next/head'
import Image from 'next/image'
import styles from '../styles/Home.module.css'
import { Auth, ThemeSupa } from '@supabase/auth-ui-react'
import { useSession, useSupabaseClient } from '@supabase/auth-helpers-react'

import Login from '../components/Login';
import Profile from '../components/Profile';
import background from '../styles/bg-masthead.jpg'

import {Helmet} from "react-helmet";

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

  return <main style={{
    background: `linear-gradient(to bottom, rgba(92, 77, 66, 0.8) 0%, rgba(92, 77, 66, 0.8) 100%), url(${background.src})`,
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
    backgroundSize: 'cover',
    }}>
    <Helmet>
        <meta charSet="utf-8" />
        <title>PodScript</title>
        <link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>📥</text></svg>"></link>
        <link rel="preconnect" href="https://fonts.googleapis.com"/>
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin/>
        <link href="https://fonts.googleapis.com/css2?family=Overpass:wght@700;800&family=Raleway:wght@300;400&display=swap" rel="stylesheet"/>
    </Helmet>
    <div className='container mx-auto grid min-h-screen text-white'>
      <div>
        <div className='text-5xl font-bold p-8'>
          📥 Podscript
        </div>
        {!session ? <Login /> : <Profile session={session} />}
      </div>
    </div>
  </main>;
}
