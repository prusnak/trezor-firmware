use super::ffi;
use core::{marker::PhantomData, mem::MaybeUninit, ptr};

pub const UZLIB_WINDOW_SIZE: usize = 1 << 10;
pub use ffi::uzlib_uncomp;

impl Default for ffi::uzlib_uncomp {
    fn default() -> Self {
        unsafe { MaybeUninit::<Self>::zeroed().assume_init() }
    }
}

pub struct UzlibContext<'a> {
    uncomp: ffi::uzlib_uncomp,
    src_data: PhantomData<&'a [u8]>,
    window: Option<[u8; UZLIB_WINDOW_SIZE]>,
}

impl<'a> UzlibContext<'a> {
    pub fn new(src: &'a [u8], use_window: bool) -> Self {
        let window = use_window.then_some([0_u8; UZLIB_WINDOW_SIZE]);

        let mut ctx = Self {
            uncomp: uzlib_uncomp::default(),
            src_data: Default::default(),
            window,
        };

        unsafe {
            ctx.uncomp.source = src.as_ptr();
            ctx.uncomp.source_limit = src.as_ptr().add(src.len());

            if let Some(w) = ctx.window {
                ffi::uzlib_uncompress_init(&mut ctx.uncomp, w.as_ptr() as _, w.len() as u32);
            } else {
                ffi::uzlib_uncompress_init(&mut ctx.uncomp, ptr::null_mut(), 0);
            }
        }

        ctx
    }

    /// returns Ok(true) if DONE
    pub fn uncompress(&mut self, dest_buf: &mut [u8]) -> Result<bool, ()> {
        unsafe {
            self.uncomp.dest = dest_buf.as_mut_ptr();
            self.uncomp.dest_limit = self.uncomp.dest.add(dest_buf.len());

            let res = ffi::uzlib_uncompress(&mut self.uncomp);

            match res {
                0 => Ok(false),
                1 => Ok(true),
                _ => Err(()),
            }
        }
    }
}
