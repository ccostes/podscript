import React from 'react';

function Card({podcast, handleSelect, classes}) {
    return(
        <li 
            // class="flex pl-2 pr-2 py-1 border-b-2 border-gray-100 rounded-xl relative cursor-pointer bg-white hover:bg-yellow-50 hover:text-gray-900"
            className={`pl-2 pr-2 py-1 relative cursor-pointer searchResult ${classes}`}
            onClick={event => handleSelect(podcast)}
            >
            <div className='flex'>
                <img className='pr-2' style={{maxWidth: 60+'px', maxHeight: 60+'px'}} src={podcast.artworkUrl60} />
                <div className=''>
                    <p className='font-semibold'>{podcast.trackName}</p>
                    {podcast.artistName}
                </div>
            </div>
        </li>
    );
}

export default Card;