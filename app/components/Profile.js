import { useState, useEffect } from 'react'
import { useUser, useSupabaseClient } from '@supabase/auth-helpers-react'

export default function Profile({ session }) {
    const [responseJson, setResponseJson] = useState({})
    const invokeNewUser = async () => {
      setResponseJson({ loading: true })
      const { data, error } = await supabase.functions.invoke('new-user', {})
      if (error) alert(error)
      setResponseJson(data)
    }
    const supabase = useSupabaseClient()

    // useEffect(() => {
    //   // invokeNewUser();
    // }, []);

    return (
    <div className='w-1/2 mx-auto p-8 place-content-center text-center text-2xl font-raleway'>
      <p>Success!<br />Your your subscription is now active! You will receive the latest episode shortly, 
      and each new episode as they are available.<br /><br />Welcome to Podscript!
      </p>
    </div>
  );
}